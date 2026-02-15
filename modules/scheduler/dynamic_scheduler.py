"""Dynamic scheduler using APScheduler for all periodic tasks."""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config.settings import settings


class DynamicScheduler:
    def __init__(self, logger=None):
        self.scheduler = AsyncIOScheduler()
        self.logger = logger
        self._jobs = {}

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def add_posting_jobs(self, publish_func, times: list[str] = None):
        """Schedule publishing at specific times (e.g. ['09:00', '14:00', '20:00'])."""
        times = times or ["09:00", "14:00", "20:00"]
        for i, time_str in enumerate(times):
            hour, minute = map(int, time_str.split(":"))
            job_id = f"post_{i}"
            self.scheduler.add_job(
                publish_func,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=job_id,
                replace_existing=True,
            )
            self._jobs[job_id] = time_str

    def add_trend_collection(self, collect_func, interval_hours: int = 2):
        """Schedule trend collection every N hours."""
        self.scheduler.add_job(
            collect_func,
            trigger=IntervalTrigger(hours=interval_hours),
            id="trend_collection",
            replace_existing=True,
        )
        self._jobs["trend_collection"] = f"every {interval_hours}h"

    def add_content_generation(self, generate_func, interval_hours: int = 4):
        """Schedule content generation every N hours."""
        self.scheduler.add_job(
            generate_func,
            trigger=IntervalTrigger(hours=interval_hours),
            id="content_generation",
            replace_existing=True,
        )
        self._jobs["content_generation"] = f"every {interval_hours}h"

    def add_metrics_collection(self, metrics_func, interval_minutes: int = 60):
        """Schedule metrics collection."""
        self.scheduler.add_job(
            metrics_func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="metrics_collection",
            replace_existing=True,
        )
        self._jobs["metrics_collection"] = f"every {interval_minutes}m"

    def add_health_check(self, health_func, interval_minutes: int = 5):
        """Schedule health checks."""
        self.scheduler.add_job(
            health_func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="health_check",
            replace_existing=True,
        )
        self._jobs["health_check"] = f"every {interval_minutes}m"

    def add_daily_report(self, report_func, time_str: str = None):
        """Schedule daily report."""
        time_str = time_str or settings.daily_report_time
        hour, minute = map(int, time_str.split(":"))
        self.scheduler.add_job(
            report_func,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_report",
            replace_existing=True,
        )
        self._jobs["daily_report"] = time_str

    def add_weekly_report(self, report_func, day: str = None, time_str: str = None):
        """Schedule weekly report."""
        day = day or settings.weekly_report_day
        time_str = time_str or settings.weekly_report_time
        hour, minute = map(int, time_str.split(":"))
        day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                    "friday": 4, "saturday": 5, "sunday": 6}
        day_num = day_map.get(day.lower(), 6)
        self.scheduler.add_job(
            report_func,
            trigger=CronTrigger(day_of_week=day_num, hour=hour, minute=minute),
            id="weekly_report",
            replace_existing=True,
        )
        self._jobs["weekly_report"] = f"{day} {time_str}"

    def add_queue_cleanup(self, cleanup_func, interval_hours: int = 6):
        """Schedule queue cleanup (expire old items)."""
        self.scheduler.add_job(
            cleanup_func,
            trigger=IntervalTrigger(hours=interval_hours),
            id="queue_cleanup",
            replace_existing=True,
        )
        self._jobs["queue_cleanup"] = f"every {interval_hours}h"

    def add_strategy_update(self, update_func, interval_hours: int = 24):
        """Schedule strategy optimization."""
        self.scheduler.add_job(
            update_func,
            trigger=IntervalTrigger(hours=interval_hours),
            id="strategy_update",
            replace_existing=True,
        )
        self._jobs["strategy_update"] = f"every {interval_hours}h"

    def update_posting_times(self, publish_func, new_times: list[str]):
        """Update posting schedule with new optimal times."""
        # Remove old posting jobs
        for key in list(self._jobs.keys()):
            if key.startswith("post_"):
                try:
                    self.scheduler.remove_job(key)
                except Exception:
                    pass
                del self._jobs[key]
        # Add new ones
        self.add_posting_jobs(publish_func, new_times)

    def get_scheduled_jobs(self) -> dict:
        return dict(self._jobs)

    def get_next_run_times(self) -> dict:
        result = {}
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                result[job.id] = next_run.strftime("%H:%M:%S %d.%m")
        return result
