"""Periodic health monitoring for all system components."""
from datetime import datetime, timedelta
from modules.database.operations import DatabaseManager
from modules.utils.groq_client import GroqClient
from modules.publisher.telegram_publisher import TelegramPublisher


class HealthMonitor:
    def __init__(self, db: DatabaseManager, groq: GroqClient,
                 publisher: TelegramPublisher, logger=None):
        self.db = db
        self.groq = groq
        self.publisher = publisher
        self.logger = logger
        self._start_time = datetime.utcnow()
        self._last_successful_post: datetime | None = None
        self._last_health_check: dict = {}

    def record_successful_post(self):
        self._last_successful_post = datetime.utcnow()

    @property
    def uptime_seconds(self) -> int:
        return int((datetime.utcnow() - self._start_time).total_seconds())

    @property
    def uptime_formatted(self) -> str:
        secs = self.uptime_seconds
        days = secs // 86400
        hours = (secs % 86400) // 3600
        minutes = (secs % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        return f"{hours}h {minutes}m"

    async def run_health_check(self) -> dict:
        """Run full health check on all components."""
        checks = {}

        # Database
        try:
            await self.db.get_queue_size()
            checks["database"] = True
        except Exception:
            checks["database"] = False

        # Groq API
        try:
            checks["groq_api"] = await self.groq.check_health()
        except Exception:
            checks["groq_api"] = False

        # Telegram Bot API
        try:
            checks["telegram_api"] = await self.publisher.check_health()
        except Exception:
            checks["telegram_api"] = False

        # Queue health
        try:
            queue_size = await self.db.get_queue_size()
            checks["queue_healthy"] = queue_size >= 5
            checks["queue_size"] = queue_size
        except Exception:
            checks["queue_healthy"] = False
            checks["queue_size"] = 0

        # Last post timing
        if self._last_successful_post:
            hours_since = (datetime.utcnow() - self._last_successful_post).total_seconds() / 3600
            checks["last_post_recent"] = hours_since < 12
            checks["hours_since_last_post"] = round(hours_since, 1)
        else:
            checks["last_post_recent"] = True  # No posts yet, not an issue
            checks["hours_since_last_post"] = None

        self._last_health_check = checks

        # Determine severity and log
        critical_components = ["database", "telegram_api"]
        critical_down = [c for c in critical_components if not checks.get(c, False)]

        if critical_down:
            if self.logger:
                status_lines = self._format_status(checks)
                await self.logger.log_critical(
                    "Critical Components Down",
                    f"Failed components:\n"
                    + "\n".join(f"  \u274c {c}" for c in critical_down)
                    + f"\n\nFull status:\n{status_lines}"
                )
        elif not all(checks.get(k, True) for k in ["groq_api", "queue_healthy"]):
            if self.logger:
                status_lines = self._format_status(checks)
                await self.logger.log_warning(
                    "Health Check Warning",
                    f"Some components degraded:\n{status_lines}"
                )

        return checks

    def _format_status(self, checks: dict) -> str:
        icons = {True: "\u2705", False: "\u274c"}
        lines = []
        for key, value in checks.items():
            if isinstance(value, bool):
                lines.append(f"{icons[value]} {key}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    def get_status_summary(self) -> dict:
        return {
            "uptime": self.uptime_formatted,
            "uptime_seconds": self.uptime_seconds,
            "last_health_check": dict(self._last_health_check),
            "last_successful_post": (
                self._last_successful_post.isoformat()
                if self._last_successful_post else None
            ),
        }
