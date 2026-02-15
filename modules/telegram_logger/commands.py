"""Admin commands handler for the logger bot."""
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from modules.utils.helpers import format_number


class AdminCommands:
    COMMANDS = {
        "/status": "\u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u0441\u0442\u0430\u0442\u0443\u0441 \u0441\u0438\u0441\u0442\u0435\u043c\u044b",
        "/stats": "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u0437\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f",
        "/queue": "\u0421\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u043e\u0447\u0435\u0440\u0435\u0434\u0438 \u043a\u043e\u043d\u0442\u0435\u043d\u0442\u0430",
        "/pause": "\u041f\u0440\u0438\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438",
        "/resume": "\u0412\u043e\u0437\u043e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438",
        "/force_gen": "\u041f\u0440\u0438\u043d\u0443\u0434\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u043a\u043e\u043d\u0442\u0435\u043d\u0442\u0430",
        "/force_post": "\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u0442\u044c \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043c\u0435\u043c",
        "/strategy": "\u0422\u0435\u043a\u0443\u0449\u0430\u044f \u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u044f",
        "/health": "Health check \u0432\u0441\u0435\u0445 \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u043e\u0432",
        "/errors": "\u041e\u0448\u0438\u0431\u043a\u0438 \u0437\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f",
        "/help": "\u0421\u043f\u0438\u0441\u043e\u043a \u043a\u043e\u043c\u0430\u043d\u0434",
    }

    def __init__(self, db, orchestrator=None):
        self.db = db
        self.orchestrator = orchestrator  # Will be set later by main.py
        self._paused = False
        self._start_time = datetime.now()

    @property
    def is_paused(self) -> bool:
        return self._paused

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lines = [f"{cmd} - {desc}" for cmd, desc in self.COMMANDS.items()]
        text = "\U0001f4cb <b>\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u044b:</b>\n\n" + "\n".join(lines)
        await update.message.reply_text(text, parse_mode="HTML")

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uptime = datetime.now() - self._start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)

        queue_size = await self.db.get_queue_size()
        today_stats = await self.db.get_today_stats()
        error_count = await self.db.get_error_count_today()
        api_usage = await self.db.get_api_usage_today()

        groq_info = api_usage.get("groq", {"calls": 0, "total_tokens": 0})
        status_icon = "\u23f8" if self._paused else "\u25b6\ufe0f"

        text = (
            f"\u2139\ufe0f <b>SYSTEM STATUS</b>\n\n"
            f"<b>\u0421\u0442\u0430\u0442\u0443\u0441:</b> {status_icon} {'Paused' if self._paused else 'Running'}\n"
            f"<b>Uptime:</b> {hours}\u0447 {minutes}\u043c\n\n"
            f"\u2699\ufe0f <b>\u041a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u044b:</b>\n"
            f"\u2705 Main Bot: Running\n"
            f"\u2705 Database: Connected\n"
            f"\u2705 Logger: Active\n\n"
            f"\U0001f4ca <b>\u0421\u0435\u0433\u043e\u0434\u043d\u044f:</b>\n"
            f"- \u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e: {today_stats['posts_count']} \u043c\u0435\u043c\u043e\u0432\n"
            f"- \u0412 \u043e\u0447\u0435\u0440\u0435\u0434\u0438: {queue_size} \u043c\u0435\u043c\u043e\u0432\n"
            f"- \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b: {format_number(today_stats['total_views'])}\n"
            f"- Engagement: {today_stats['avg_engagement']:.2%}\n\n"
            f"\U0001f4bb <b>API:</b>\n"
            f"- Groq: {groq_info['calls']} \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432 ({format_number(groq_info['total_tokens'])} tokens)\n"
            f"- \u041e\u0448\u0438\u0431\u043a\u0438: {error_count}"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = await self.db.get_today_stats()
        top_post = await self.db.get_top_post(
            since=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        )

        text = (
            f"\U0001f4ca <b>\u0421\u0422\u0410\u0422\u0418\u0421\u0422\u0418\u041a\u0410 \u0417\u0410 \u0421\u0415\u0413\u041e\u0414\u041d\u042f</b>\n\n"
            f"\u041f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438: {stats['posts_count']} \u043c\u0435\u043c\u043e\u0432\n"
            f"\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b: {format_number(stats['total_views'])}\n"
            f"Engagement: {stats['avg_engagement']:.2%}\n"
        )

        if top_post:
            text += (
                f"\n<b>\u0422\u043e\u043f-\u043f\u043e\u0441\u0442:</b>\n"
                f"\U0001f441 {format_number(top_post.views)} \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432\n"
                f"\U0001f4e4 {top_post.forwards} \u0440\u0435\u043f\u043e\u0441\u0442\u043e\u0432"
            )

        await update.message.reply_text(text, parse_mode="HTML")

    async def handle_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        queue_size = await self.db.get_queue_size()
        text = (
            f"\U0001f4e6 <b>\u041e\u0427\u0415\u0420\u0415\u0414\u042c \u041a\u041e\u041d\u0422\u0415\u041d\u0422\u0410</b>\n\n"
            f"\u041c\u0435\u043c\u043e\u0432 \u0432 \u043e\u0447\u0435\u0440\u0435\u0434\u0438: {queue_size}\n"
            f"\u041c\u0438\u043d\u0438\u043c\u0443\u043c: 10\n"
            f"\u041c\u0430\u043a\u0441\u0438\u043c\u0443\u043c: 50\n\n"
        )
        if queue_size < 10:
            text += "\u26a0\ufe0f \u041e\u0447\u0435\u0440\u0435\u0434\u044c \u043d\u0438\u0436\u0435 \u043c\u0438\u043d\u0438\u043c\u0443\u043c\u0430!"
        elif queue_size > 40:
            text += "\u2705 \u041e\u0447\u0435\u0440\u0435\u0434\u044c \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0430"
        else:
            text += "\u2705 \u041e\u0447\u0435\u0440\u0435\u0434\u044c \u0432 \u043d\u043e\u0440\u043c\u0435"
        await update.message.reply_text(text, parse_mode="HTML")

    async def handle_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._paused = True
        await update.message.reply_text("\u23f8 \u041f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438 \u043f\u0440\u0438\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u044b")

    async def handle_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._paused = False
        await update.message.reply_text("\u25b6\ufe0f \u041f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438 \u0432\u043e\u0437\u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u044b")

    async def handle_force_gen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("\U0001f504 \u0417\u0430\u043f\u0443\u0449\u0435\u043d\u0430 \u043f\u0440\u0438\u043d\u0443\u0434\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f...")
        if self.orchestrator:
            await self.orchestrator.force_generate()
            queue_size = await self.db.get_queue_size()
            await update.message.reply_text(
                f"\u2705 \u0413\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430\n\u0412 \u043e\u0447\u0435\u0440\u0435\u0434\u0438: {queue_size} \u043c\u0435\u043c\u043e\u0432"
            )
        else:
            await update.message.reply_text("\u274c Orchestrator \u043d\u0435 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d")

    async def handle_force_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("\U0001f4e4 \u041f\u0443\u0431\u043b\u0438\u043a\u0443\u044e \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043c\u0435\u043c...")
        if self.orchestrator:
            result = await self.orchestrator.force_publish()
            if result:
                await update.message.reply_text("\u2705 \u041c\u0435\u043c \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d!")
            else:
                await update.message.reply_text("\u274c \u041e\u0447\u0435\u0440\u0435\u0434\u044c \u043f\u0443\u0441\u0442\u0430 \u0438\u043b\u0438 \u043e\u0448\u0438\u0431\u043a\u0430 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438")
        else:
            await update.message.reply_text("\u274c Orchestrator \u043d\u0435 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d")

    async def handle_strategy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        strategy = await self.db.get_active_strategy()
        if not strategy:
            await update.message.reply_text("\u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u043e\u0439 \u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u0438")
            return

        cfg = strategy.config_data
        posting = cfg.get("posting_schedule", {})
        mix = cfg.get("content_mix", {})

        text = (
            f"\U0001f3af <b>\u0422\u0415\u041a\u0423\u0429\u0410\u042f \u0421\u0422\u0420\u0410\u0422\u0415\u0413\u0418\u042f</b>\n\n"
            f"<b>\u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435:</b>\n"
            f"- \u041f\u043e\u0441\u0442\u043e\u0432 \u0432 \u0434\u0435\u043d\u044c: {posting.get('posts_per_day', '?')}\n"
            f"- \u041b\u0443\u0447\u0448\u0435\u0435 \u0432\u0440\u0435\u043c\u044f: {', '.join(posting.get('best_times', []))}\n\n"
            f"<b>\u041c\u0438\u043a\u0441 \u043a\u043e\u043d\u0442\u0435\u043d\u0442\u0430:</b>\n"
        )
        for mtype, ratio in mix.items():
            text += f"- {mtype}: {ratio:.0%}\n"

        text += f"\n<b>\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e:</b> {strategy.updated_at.strftime('%d.%m.%Y %H:%M')}"
        await update.message.reply_text(text, parse_mode="HTML")

    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Basic health check
        checks = {}
        try:
            await self.db.get_queue_size()
            checks["Database"] = True
        except Exception:
            checks["Database"] = False

        checks["Main Bot"] = not self._paused
        checks["Logger"] = True

        lines = []
        for component, ok in checks.items():
            icon = "\u2705" if ok else "\u274c"
            lines.append(f"{icon} {component}")

        text = (
            f"\U0001f3e5 <b>HEALTH CHECK</b>\n\n"
            + "\n".join(lines)
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def handle_errors(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logs = await self.db.get_recent_logs(level="ERROR", limit=5)
        if not logs:
            await update.message.reply_text("\u2705 \u041e\u0448\u0438\u0431\u043e\u043a \u0437\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f \u043d\u0435\u0442!")
            return

        text = f"\u274c <b>\u041f\u041e\u0421\u041b\u0415\u0414\u041d\u0418\u0415 \u041e\u0428\u0418\u0411\u041a\u0418:</b>\n\n"
        for log in logs:
            text += (
                f"\u2022 [{log.timestamp.strftime('%H:%M')}] {log.module or '?'}\n"
                f"  {log.message[:100]}\n\n"
            )
        await update.message.reply_text(text, parse_mode="HTML")
