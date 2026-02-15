"""Collect post metrics from Telegram channel."""
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
from config.settings import settings
from modules.database.operations import DatabaseManager


class MetricsCollector:
    def __init__(self, db: DatabaseManager, logger=None):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.channel_id = settings.telegram_channel_id
        self.db = db
        self.logger = logger

    async def collect_for_recent_posts(self):
        """Collect metrics for posts published in the last 24h."""
        since = datetime.utcnow() - timedelta(hours=24)
        posts = await self.db.get_posts_since(since)

        for post in posts:
            if not post.telegram_message_id:
                continue
            await self._update_post_metrics(post)

    async def _update_post_metrics(self, post):
        """Fetch and update metrics for a single post."""
        try:
            # Note: Telegram Bot API doesn't provide view counts directly.
            # For channels, we can approximate using forwarded message counts.
            # Full stats require the Telegram Statistics API (channel admin).
            # Here we simulate a basic metrics update structure.

            # In a production setup, you would use:
            # - Telethon or Pyrogram for full channel stats
            # - Or Telegram Bot API getChat for subscriber count
            # For now, we track what's available through the bot API.

            elapsed = datetime.utcnow() - (post.published_at or datetime.utcnow())
            elapsed_hours = elapsed.total_seconds() / 3600

            # Calculate performance score based on available data
            views = post.views or 0
            forwards = post.forwards or 0
            reactions = post.reactions or {}
            total_reactions = sum(reactions.values()) if isinstance(reactions, dict) else 0

            engagement_rate = 0.0
            if views > 0:
                engagement_rate = (forwards + total_reactions) / views

            # Simple performance score (0-10)
            performance = min(10.0, (
                (views / 1000) * 2 +
                forwards * 0.5 +
                total_reactions * 0.1 +
                engagement_rate * 20
            ))

            await self.db.update_post_metrics(
                post.id,
                engagement_rate=engagement_rate,
                performance_score=round(performance, 1),
            )

            # Log metrics at key intervals (1h, 6h, 24h)
            if self.logger and elapsed_hours in range(1, 2) or elapsed_hours in range(6, 7):
                reactions_str = " | ".join(f"{k} {v}" for k, v in reactions.items()) if reactions else "N/A"
                await self.logger.log_post_metrics(
                    post.id,
                    {
                        "time_elapsed": f"{int(elapsed_hours)} hours",
                        "views": views,
                        "views_growth": 0,
                        "forwards": forwards,
                        "comments": post.comments or 0,
                        "reactions": reactions,
                        "engagement_rate": engagement_rate,
                        "performance_score": round(performance, 1),
                    }
                )

        except Exception as e:
            if self.logger:
                await self.logger.log_warning(
                    "Metrics Collection Error",
                    f"Post {post.id}: {e}"
                )

    async def get_average_metrics(self, days: int = 7) -> dict:
        """Get average metrics over the last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        posts = await self.db.get_posts_since(since)

        if not posts:
            return {"avg_views": 0, "avg_forwards": 0, "avg_engagement": 0.0,
                    "avg_performance": 0.0, "total_posts": 0}

        published = [p for p in posts if p.published_at]
        if not published:
            return {"avg_views": 0, "avg_forwards": 0, "avg_engagement": 0.0,
                    "avg_performance": 0.0, "total_posts": 0}

        return {
            "avg_views": sum(p.views or 0 for p in published) // len(published),
            "avg_forwards": sum(p.forwards or 0 for p in published) // len(published),
            "avg_engagement": sum(p.engagement_rate or 0 for p in published) / len(published),
            "avg_performance": sum(p.performance_score or 0 for p in published) / len(published),
            "total_posts": len(published),
        }

    async def get_best_content_types(self, days: int = 14) -> dict:
        """Analyze which content types perform best."""
        since = datetime.utcnow() - timedelta(days=days)
        posts = await self.db.get_posts_since(since)

        type_stats = {}
        for post in posts:
            if not post.published_at:
                continue
            ct = post.content_type or "unknown"
            if ct not in type_stats:
                type_stats[ct] = {"count": 0, "total_performance": 0, "total_engagement": 0}
            type_stats[ct]["count"] += 1
            type_stats[ct]["total_performance"] += (post.performance_score or 0)
            type_stats[ct]["total_engagement"] += (post.engagement_rate or 0)

        for ct in type_stats:
            n = type_stats[ct]["count"]
            if n > 0:
                type_stats[ct]["avg_performance"] = type_stats[ct]["total_performance"] / n
                type_stats[ct]["avg_engagement"] = type_stats[ct]["total_engagement"] / n

        return type_stats
