"""
Centralized Telegram logging system.
Sends all events, metrics, and errors to a separate admin Telegram chat.
"""
import asyncio
import traceback
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from config.settings import settings
from .formatters import LogFormatter
from .rate_limiter import LogRateLimiter


class TelegramLogger:
    LOG_LEVELS = {
        "DEBUG": "\U0001f50d",
        "INFO": "\u2139\ufe0f",
        "SUCCESS": "\u2705",
        "WARNING": "\u26a0\ufe0f",
        "ERROR": "\u274c",
        "CRITICAL": "\U0001f6a8",
    }

    def __init__(self):
        self.bot = Bot(token=settings.logger_bot_token)
        self.admin_chat_id = settings.admin_chat_id
        self.enabled = settings.enable_telegram_logging
        self.formatter = LogFormatter()
        self.rate_limiter = LogRateLimiter()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._started = False

    async def start(self):
        if self._started:
            return
        self._started = True
        self._worker_task = asyncio.create_task(self._process_queue())

    async def stop(self):
        self._started = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        # Flush remaining messages
        while not self._queue.empty():
            msg = self._queue.get_nowait()
            await self._send_message(msg)

    async def _process_queue(self):
        while self._started:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._send_message(message)
                await asyncio.sleep(0.1)  # Rate limit: ~10 msg/sec max
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    async def _send_message(self, text: str):
        if not self.enabled:
            return
        try:
            # Telegram message limit is 4096 chars
            if len(text) > 4096:
                text = text[:4090] + "\n..."
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except TelegramError:
            pass  # Can't log a logging failure to Telegram

    async def _enqueue(self, level: str, message: str, urgent: bool = False):
        if not self.enabled:
            return
        if urgent:
            await self._send_message(message)
        else:
            should_send = self.rate_limiter.should_send(level, message)
            if should_send:
                await self._queue.put(message)

    # ─── Public API ────────────────────────────────────────────────

    async def log_system_event(self, event_type: str, details: str):
        msg = self.formatter.format_system_event(event_type, details)
        await self._enqueue("INFO", msg)

    async def log_successful_post(self, post_data: dict):
        msg = self.formatter.format_successful_post(post_data)
        await self._enqueue("SUCCESS", msg)

    async def log_post_metrics(self, post_id: int | str, metrics: dict):
        msg = self.formatter.format_post_metrics(post_id, metrics)
        await self._enqueue("INFO", msg)

    async def log_warning(self, warning_type: str, details: str):
        msg = self.formatter.format_warning(warning_type, details)
        await self._enqueue("WARNING", msg, urgent=True)

    async def log_error(self, error_type: str, error: Exception, context: dict = None):
        tb = traceback.format_exc() if context is None else context.get("traceback", "")
        msg = self.formatter.format_error(error_type, error, tb, context)
        await self._enqueue("ERROR", msg, urgent=True)

    async def log_critical(self, critical_type: str, details: str):
        msg = self.formatter.format_critical(critical_type, details)
        await self._enqueue("CRITICAL", msg, urgent=True)

    async def log_info(self, title: str, details: str):
        msg = self.formatter.format_info(title, details)
        await self._enqueue("INFO", msg)

    async def log_strategy_update(self, old_strategy: dict, new_strategy: dict, reason: str):
        msg = self.formatter.format_strategy_update(old_strategy, new_strategy, reason)
        await self._enqueue("INFO", msg)

    async def log_ab_test_results(self, test_data: dict):
        msg = self.formatter.format_ab_test_results(test_data)
        await self._enqueue("INFO", msg)

    async def log_anomaly(self, anomaly_data: dict):
        msg = self.formatter.format_anomaly(anomaly_data)
        await self._enqueue("WARNING", msg, urgent=True)

    async def send_daily_report(self, stats: dict):
        msg = self.formatter.format_daily_report(stats)
        await self._send_message(msg)  # Reports always sent immediately

    async def send_weekly_report(self, stats: dict):
        msg = self.formatter.format_weekly_report(stats)
        await self._send_message(msg)

    async def send_raw(self, text: str):
        """Send raw HTML message directly."""
        await self._send_message(text)
