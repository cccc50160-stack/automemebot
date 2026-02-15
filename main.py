"""
AutoMemeBot v3.0 — Main Orchestrator
Fully autonomous Telegram meme bot with logging.
"""
import sys
import asyncio
import traceback
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from telegram.ext import Application, CommandHandler

from config.settings import settings
from modules.database.operations import DatabaseManager
from modules.telegram_logger.logger import TelegramLogger
from modules.telegram_logger.commands import AdminCommands
from modules.telegram_logger.reports import ReportGenerator
from modules.utils.groq_client import GroqClient
from modules.content_generator.idea_generator import IdeaGenerator
from modules.content_generator.quality_filter import QualityFilter
from modules.content_generator.visual_generator import VisualGenerator
from modules.trend_collector.groq_trends import GroqTrendCollector
from modules.trend_collector.aggregator import TrendAggregator
from modules.publisher.telegram_publisher import TelegramPublisher
from modules.publisher.post_logic import PostingPipeline
from modules.scheduler.dynamic_scheduler import DynamicScheduler
from modules.scheduler.queue_manager import QueueManager
from modules.analytics.metrics_collector import MetricsCollector
from modules.analytics.learning_algo import LearningAlgorithm
from modules.error_handler.health_monitor import HealthMonitor
from modules.error_handler.fallback_strategies import APIFallbackStrategy, RateLimitHandler
from modules.error_handler.recovery import RecoveryManager


class Orchestrator:
    """Main orchestrator that wires and controls all modules."""

    def __init__(self):
        # ── Core services ──────────────────────────────────────
        self.db = DatabaseManager()
        self.logger = TelegramLogger()
        self.groq = GroqClient(db=self.db, logger=self.logger)

        # ── Content pipeline ───────────────────────────────────
        self.idea_gen = IdeaGenerator(self.groq, self.logger)
        self.quality_filter = QualityFilter(self.groq, self.logger)
        self.visual_gen = VisualGenerator(self.logger)

        # ── Trends ─────────────────────────────────────────────
        self.groq_trends = GroqTrendCollector(self.groq, self.logger)
        self.trend_aggregator = TrendAggregator(self.groq_trends, self.db, self.logger)

        # ── Publishing ─────────────────────────────────────────
        self.publisher = TelegramPublisher(self.logger)
        self.posting_pipeline = PostingPipeline(self.db, self.publisher, self.visual_gen, self.logger)
        self.queue_manager = QueueManager(self.db, self.logger)

        # ── Analytics ──────────────────────────────────────────
        self.metrics = MetricsCollector(self.db, self.logger)
        self.learning = LearningAlgorithm(self.db, self.groq, self.metrics, self.logger)

        # ── Scheduler ──────────────────────────────────────────
        self.scheduler = DynamicScheduler(self.logger)

        # ── Error handling ─────────────────────────────────────
        self.health_monitor = HealthMonitor(self.db, self.groq, self.publisher, self.logger)
        self.fallback = APIFallbackStrategy(self.logger)
        self.rate_limiter = RateLimitHandler(self.logger)
        self.recovery = RecoveryManager(self.logger)

        # ── Reports ────────────────────────────────────────────
        self.report_gen = ReportGenerator(self.db)

        # ── Admin commands (for logger bot) ────────────────────
        self.admin_commands = AdminCommands(self.db, orchestrator=self)

        # ── Logger bot app ─────────────────────────────────────
        self.logger_app: Application | None = None

    # ═══════════════════════════════════════════════════════════
    #  STARTUP
    # ═══════════════════════════════════════════════════════════

    async def start(self):
        """Initialize everything and start the bot."""
        try:
            # 1. Init database
            await self.db.init_db()
            print("[OK] Database initialized")

            # 2. Start logger
            await self.logger.start()
            print("[OK] Telegram Logger started")

            # 3. Ensure default strategy
            await self.learning.ensure_strategy_exists()
            print("[OK] Strategy loaded")

            # 4. Setup scheduler
            await self._setup_scheduler()
            print("[OK] Scheduler started")

            # 5. Start logger bot (for admin commands)
            await self._start_logger_bot()
            print("[OK] Logger bot started")

            # 6. Send startup notification
            await self.logger.log_system_event(
                "Bot Started",
                "AutoMemeBot v3.0 is now running.\n"
                f"Channel: {settings.telegram_channel_id}\n"
                f"Posts/day: {settings.posts_per_day}\n"
                f"Groq model: {settings.groq_model}\n"
                f"Queue min/max: {settings.min_queue_size}/{settings.max_queue_size}"
            )

            # 7. Initial content generation if queue is low
            if await self.queue_manager.needs_refill():
                print("[...] Queue low, generating initial content...")
                await self.generate_content_batch()
                print("[OK] Initial content generated")

            print("\n=== AutoMemeBot is running ===\n")

        except Exception as e:
            print(f"[FATAL] Startup failed: {e}")
            traceback.print_exc()
            raise

    async def stop(self):
        """Graceful shutdown."""
        try:
            await self.logger.log_system_event("Bot Stopping", "Graceful shutdown initiated.")
        except Exception:
            pass

        self.scheduler.stop()
        await self.logger.stop()
        await self.db.close()

        if self.logger_app:
            await self.logger_app.stop()
            await self.logger_app.shutdown()

        print("[OK] Bot stopped")

    # ═══════════════════════════════════════════════════════════
    #  SCHEDULER SETUP
    # ═══════════════════════════════════════════════════════════

    async def _setup_scheduler(self):
        """Configure all scheduled jobs."""
        strategy = await self.learning.get_current_strategy()
        posting_schedule = strategy.get("posting_schedule", {})
        times = posting_schedule.get("best_times", ["09:00", "14:00", "20:00"])

        self.scheduler.add_posting_jobs(self.scheduled_publish, times)
        self.scheduler.add_trend_collection(self.collect_trends, interval_hours=2)
        self.scheduler.add_content_generation(self.generate_content_batch, interval_hours=4)
        self.scheduler.add_metrics_collection(self.collect_metrics, interval_minutes=60)
        self.scheduler.add_health_check(self.run_health_check, interval_minutes=5)
        self.scheduler.add_queue_cleanup(self.cleanup_queue, interval_hours=6)
        self.scheduler.add_strategy_update(self.update_strategy, interval_hours=24)
        self.scheduler.add_daily_report(self.send_daily_report)
        self.scheduler.add_weekly_report(self.send_weekly_report)

        self.scheduler.start()

    # ═══════════════════════════════════════════════════════════
    #  LOGGER BOT (admin commands)
    # ═══════════════════════════════════════════════════════════

    async def _start_logger_bot(self):
        """Start the logger bot to receive admin commands."""
        self.logger_app = (
            Application.builder()
            .token(settings.logger_bot_token)
            .build()
        )

        cmds = self.admin_commands
        self.logger_app.add_handler(CommandHandler("help", cmds.handle_help))
        self.logger_app.add_handler(CommandHandler("start", cmds.handle_help))
        self.logger_app.add_handler(CommandHandler("status", cmds.handle_status))
        self.logger_app.add_handler(CommandHandler("stats", cmds.handle_stats))
        self.logger_app.add_handler(CommandHandler("queue", cmds.handle_queue))
        self.logger_app.add_handler(CommandHandler("pause", cmds.handle_pause))
        self.logger_app.add_handler(CommandHandler("resume", cmds.handle_resume))
        self.logger_app.add_handler(CommandHandler("force_gen", cmds.handle_force_gen))
        self.logger_app.add_handler(CommandHandler("force_post", cmds.handle_force_post))
        self.logger_app.add_handler(CommandHandler("strategy", cmds.handle_strategy))
        self.logger_app.add_handler(CommandHandler("health", cmds.handle_health))
        self.logger_app.add_handler(CommandHandler("errors", cmds.handle_errors))

        await self.logger_app.initialize()
        await self.logger_app.start()
        await self.logger_app.updater.start_polling(drop_pending_updates=True)

    # ═══════════════════════════════════════════════════════════
    #  SCHEDULED TASKS
    # ═══════════════════════════════════════════════════════════

    async def scheduled_publish(self):
        """Called by scheduler at posting times."""
        if self.admin_commands.is_paused:
            await self.logger.log_info("Publish Skipped", "Publishing is paused by admin.")
            return

        success = await self.posting_pipeline.publish_next()
        if success:
            self.health_monitor.record_successful_post()

        # Refill queue if needed
        if await self.queue_manager.needs_refill():
            await self.generate_content_batch()

    async def collect_trends(self):
        """Collect trends from all sources."""
        try:
            trends = await self.trend_aggregator.collect_all()
            await self.logger.log_system_event(
                "Trends Updated",
                f"Collected {len(trends)} trends"
            )
        except Exception as e:
            await self.logger.log_error(
                "Trend Collection Failed", e,
                {"module": "orchestrator", "function": "collect_trends",
                 "traceback": traceback.format_exc()}
            )

    async def generate_content_batch(self):
        """Generate a batch of memes from current trends."""
        try:
            trends = await self.db.get_unused_trends(limit=3)
            if not trends:
                # Generate fresh trends first
                await self.collect_trends()
                trends = await self.db.get_unused_trends(limit=3)

            if not trends:
                await self.logger.log_warning(
                    "No Trends Available",
                    "Cannot generate content without trends."
                )
                return

            total_added = 0
            total_rejected = 0

            for trend in trends:
                ideas = await self.idea_gen.generate_ideas(
                    trend_topic=trend.topic,
                    keywords=trend.keywords or [],
                    context=trend.context or "",
                    count=5,
                )

                for idea in ideas:
                    quality = await self.quality_filter.check_quality(idea)

                    if quality["passed"]:
                        # Add scores to meme data
                        idea["quality_score"] = quality["scores"].get("humor", 5)
                        idea["humor_score"] = quality["scores"].get("humor", 5)
                        idea["relevance_score"] = quality["scores"].get("relevance", 5)

                        # Pre-generate images for visual memes
                        if idea.get("type") != "text_only":
                            image_path = await self.visual_gen.generate(idea)
                            if image_path:
                                idea["image_path"] = image_path

                        priority = self.quality_filter.calculate_priority(idea, quality["scores"])
                        added = await self.queue_manager.add_meme(idea, priority)
                        if added:
                            total_added += 1
                    else:
                        total_rejected += 1

                await self.db.increment_trend_usage(trend.id)

            await self.logger.log_system_event(
                "Content Generation Completed",
                f"Added: {total_added} memes to queue\n"
                f"Rejected: {total_rejected} (quality filter)\n"
                f"Queue size: {await self.queue_manager.get_size()}"
            )

        except Exception as e:
            await self.logger.log_error(
                "Content Generation Failed", e,
                {"module": "orchestrator", "function": "generate_content_batch",
                 "traceback": traceback.format_exc()}
            )

    async def collect_metrics(self):
        """Collect metrics for recently published posts."""
        try:
            await self.metrics.collect_for_recent_posts()
        except Exception as e:
            await self.logger.log_warning(
                "Metrics Collection Error",
                f"Error: {e}"
            )

    async def run_health_check(self):
        """Run periodic health check."""
        try:
            await self.health_monitor.run_health_check()
        except Exception as e:
            await self.logger.log_warning(
                "Health Check Error",
                f"Error: {e}"
            )

    async def cleanup_queue(self):
        """Expire old queue items."""
        try:
            expired = await self.queue_manager.cleanup_expired()
            if expired > 0:
                await self.logger.log_system_event(
                    "Queue Cleanup",
                    f"Expired {expired} old items"
                )
        except Exception:
            pass

    async def update_strategy(self):
        """Run learning algorithm to update strategy."""
        try:
            result = await self.learning.analyze_and_update()
            if result:
                # Update posting schedule if changed
                posting = result.get("posting_schedule", {})
                new_times = posting.get("best_times")
                if new_times:
                    self.scheduler.update_posting_times(self.scheduled_publish, new_times)
        except Exception as e:
            await self.logger.log_warning(
                "Strategy Update Error",
                f"Error: {e}"
            )

    async def send_daily_report(self):
        """Generate and send daily report."""
        try:
            stats = await self.report_gen.generate_daily_stats()
            stats["uptime"] = self.health_monitor.uptime_formatted
            await self.logger.send_daily_report(stats)
        except Exception as e:
            await self.logger.log_warning("Daily Report Error", f"Error: {e}")

    async def send_weekly_report(self):
        """Generate and send weekly report."""
        try:
            stats = await self.report_gen.generate_weekly_stats()
            stats["weekly_uptime"] = self.health_monitor.uptime_formatted
            await self.logger.send_weekly_report(stats)
        except Exception as e:
            await self.logger.log_warning("Weekly Report Error", f"Error: {e}")

    # ═══════════════════════════════════════════════════════════
    #  MANUAL TRIGGERS (called from admin commands)
    # ═══════════════════════════════════════════════════════════

    async def force_generate(self):
        """Force content generation (from admin command)."""
        await self.generate_content_batch()

    async def force_publish(self) -> bool:
        """Force publish next meme (from admin command)."""
        success = await self.posting_pipeline.publish_next()
        if success:
            self.health_monitor.record_successful_post()
        return success


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def main():
    bot = Orchestrator()

    try:
        await bot.start()

        # Keep running
        print("Press Ctrl+C to stop...")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\n[FATAL] {e}")
        traceback.print_exc()
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
