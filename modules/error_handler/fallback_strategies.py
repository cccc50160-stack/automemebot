"""API fallback chains and rate limit handling."""
import asyncio
from datetime import datetime, timedelta


class APIFallbackStrategy:
    """Manages fallback chains when primary APIs fail."""

    def __init__(self, logger=None):
        self.logger = logger
        self._failure_counts: dict[str, int] = {}
        self._last_failure: dict[str, datetime] = {}
        self._circuit_open: dict[str, datetime] = {}
        self.circuit_breaker_threshold = 5  # failures before opening circuit
        self.circuit_breaker_timeout = 300  # seconds before retrying

    def record_failure(self, service: str):
        """Record an API failure."""
        self._failure_counts[service] = self._failure_counts.get(service, 0) + 1
        self._last_failure[service] = datetime.utcnow()

        if self._failure_counts[service] >= self.circuit_breaker_threshold:
            self._circuit_open[service] = datetime.utcnow()

    def record_success(self, service: str):
        """Record an API success — reset failure counter."""
        self._failure_counts[service] = 0
        self._circuit_open.pop(service, None)

    def is_available(self, service: str) -> bool:
        """Check if a service is considered available (circuit breaker)."""
        if service not in self._circuit_open:
            return True

        elapsed = (datetime.utcnow() - self._circuit_open[service]).total_seconds()
        if elapsed >= self.circuit_breaker_timeout:
            # Allow a retry (half-open state)
            return True

        return False

    def get_failure_count(self, service: str) -> int:
        return self._failure_counts.get(service, 0)

    async def execute_with_fallback(self, primary_func, fallback_funcs: list,
                                     service_name: str = "unknown"):
        """
        Try primary function, then fallbacks in order.
        Returns the first successful result.
        """
        # Try primary
        if self.is_available(service_name):
            try:
                result = await primary_func()
                self.record_success(service_name)
                return result
            except Exception as e:
                self.record_failure(service_name)
                if self.logger:
                    await self.logger.log_warning(
                        f"{service_name} Primary Failed",
                        f"Error: {e}\nTrying fallbacks..."
                    )

        # Try fallbacks
        for i, fallback in enumerate(fallback_funcs):
            fallback_name = f"{service_name}_fallback_{i}"
            try:
                result = await fallback()
                if self.logger:
                    await self.logger.log_info(
                        "Fallback Successful",
                        f"Service: {service_name}\nFallback #{i + 1} worked"
                    )
                return result
            except Exception as e:
                if self.logger:
                    await self.logger.log_warning(
                        f"Fallback #{i + 1} Failed",
                        f"Service: {service_name}\nError: {e}"
                    )
                continue

        # All failed
        if self.logger:
            await self.logger.log_critical(
                "All Fallbacks Failed",
                f"Service: {service_name}\n"
                f"Primary + {len(fallback_funcs)} fallbacks all failed.\n"
                f"Total failures: {self.get_failure_count(service_name)}"
            )
        return None


class RateLimitHandler:
    """Track and manage API rate limits."""

    def __init__(self, logger=None):
        self.logger = logger
        self._usage: dict[str, dict] = {}
        self._limits: dict[str, dict] = {
            "groq": {"rpm": 30, "rpd": 14400, "window_minutes": 1},
            "telegram": {"rpm": 30, "window_minutes": 1},
            "huggingface": {"rpm": 10, "window_minutes": 1},
        }

    def record_request(self, service: str):
        """Record an API request."""
        now = datetime.utcnow()
        if service not in self._usage:
            self._usage[service] = {"requests": [], "daily_count": 0, "daily_reset": now}

        entry = self._usage[service]
        entry["requests"].append(now)
        entry["daily_count"] += 1

        # Reset daily counter if needed
        if (now - entry["daily_reset"]).total_seconds() > 86400:
            entry["daily_count"] = 1
            entry["daily_reset"] = now

        # Cleanup old requests (keep last 5 minutes)
        cutoff = now - timedelta(minutes=5)
        entry["requests"] = [r for r in entry["requests"] if r > cutoff]

    def get_usage_percentage(self, service: str) -> float:
        """Get current usage as percentage of limit."""
        if service not in self._limits or service not in self._usage:
            return 0.0

        limit = self._limits[service]
        entry = self._usage[service]
        window = timedelta(minutes=limit.get("window_minutes", 1))
        cutoff = datetime.utcnow() - window

        recent = [r for r in entry["requests"] if r > cutoff]
        rpm = limit.get("rpm", 30)

        return (len(recent) / rpm) * 100

    async def wait_if_needed(self, service: str):
        """Wait if we're close to rate limit."""
        usage_pct = self.get_usage_percentage(service)

        if usage_pct >= 90:
            wait_time = 60  # Wait a full minute
            if self.logger:
                await self.logger.log_warning(
                    "Rate Limit Throttling",
                    f"Service: {service}\n"
                    f"Usage: {usage_pct:.0f}%\n"
                    f"Waiting {wait_time}s..."
                )
            await asyncio.sleep(wait_time)
        elif usage_pct >= 70:
            await asyncio.sleep(5)

    def get_all_usage(self) -> dict:
        """Get usage stats for all services."""
        result = {}
        for service in self._limits:
            result[service] = {
                "usage_percent": round(self.get_usage_percentage(service), 1),
                "daily_count": self._usage.get(service, {}).get("daily_count", 0),
                "daily_limit": self._limits[service].get("rpd", "unlimited"),
            }
        return result
