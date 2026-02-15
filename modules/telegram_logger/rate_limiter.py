"""Rate limiter for log messages to avoid Telegram spam."""
import hashlib
from datetime import datetime


class LogRateLimiter:
    TIME_WINDOWS = {
        "DEBUG": 600,      # 10 min
        "INFO": 300,       # 5 min
        "SUCCESS": 600,    # 10 min
        "WARNING": 120,    # 2 min
        "ERROR": 0,        # No limit
        "CRITICAL": 0,     # No limit
    }

    def __init__(self):
        self._counters: dict[str, dict] = {}

    def _hash(self, message: str) -> str:
        return hashlib.md5(message.encode()).hexdigest()[:12]

    def should_send(self, level: str, message: str) -> bool:
        """Check if this log message should be sent now."""
        if level in ("ERROR", "CRITICAL"):
            return True

        window = self.TIME_WINDOWS.get(level, 300)
        if window == 0:
            return True

        msg_hash = self._hash(message)
        key = f"{level}:{msg_hash}"
        now = datetime.now()

        if key not in self._counters:
            self._counters[key] = {
                "count": 1,
                "first_seen": now,
                "last_sent": now,
            }
            return True

        entry = self._counters[key]
        elapsed = (now - entry["last_sent"]).total_seconds()

        if elapsed >= window:
            count = entry["count"]
            self._counters[key] = {
                "count": 1,
                "first_seen": now,
                "last_sent": now,
            }
            return True

        entry["count"] += 1
        return False

    def cleanup(self):
        """Remove stale entries older than 1 hour."""
        now = datetime.now()
        stale_keys = [
            k for k, v in self._counters.items()
            if (now - v["last_sent"]).total_seconds() > 3600
        ]
        for k in stale_keys:
            del self._counters[k]
