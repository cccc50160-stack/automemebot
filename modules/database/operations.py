from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, delete, func, desc
from .models import Base, Post, Trend, ContentQueue, StrategyConfig, SystemLog, ApiUsage
from config.settings import settings


class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        await self.engine.dispose()

    # ─── Posts ─────────────────────────────────────────────────────

    async def save_post(self, **kwargs) -> Post:
        async with self.session_factory() as session:
            post = Post(**kwargs)
            session.add(post)
            await session.commit()
            await session.refresh(post)
            return post

    async def update_post_metrics(self, post_id: int, **kwargs):
        async with self.session_factory() as session:
            await session.execute(
                update(Post).where(Post.id == post_id).values(**kwargs)
            )
            await session.commit()

    async def get_post_by_message_id(self, message_id: int) -> Optional[Post]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post).where(Post.telegram_message_id == message_id)
            )
            return result.scalar_one_or_none()

    async def get_recent_posts(self, limit: int = 50) -> list[Post]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post).order_by(desc(Post.published_at)).limit(limit)
            )
            return list(result.scalars().all())

    async def get_posts_since(self, since: datetime) -> list[Post]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post)
                .where(Post.published_at >= since)
                .order_by(desc(Post.published_at))
            )
            return list(result.scalars().all())

    async def get_top_post(self, since: datetime) -> Optional[Post]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post)
                .where(Post.published_at >= since)
                .order_by(desc(Post.performance_score))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_worst_post(self, since: datetime) -> Optional[Post]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post)
                .where(Post.published_at >= since, Post.performance_score.isnot(None))
                .order_by(Post.performance_score)
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_posts_needing_metrics(self, hours_since: list[int]) -> list[Post]:
        """Get posts that need metrics collected at specific hour marks."""
        async with self.session_factory() as session:
            posts = []
            for hours in hours_since:
                target_time = datetime.utcnow() - timedelta(hours=hours)
                window_start = target_time - timedelta(minutes=10)
                window_end = target_time + timedelta(minutes=10)
                result = await session.execute(
                    select(Post).where(
                        Post.published_at.between(window_start, window_end)
                    )
                )
                posts.extend(result.scalars().all())
            return posts

    # ─── Trends ────────────────────────────────────────────────────

    async def save_trends(self, trends: list[dict]) -> list[Trend]:
        async with self.session_factory() as session:
            trend_objects = [Trend(**t) for t in trends]
            session.add_all(trend_objects)
            await session.commit()
            for t in trend_objects:
                await session.refresh(t)
            return trend_objects

    async def get_latest_trends(self, limit: int = 10) -> list[Trend]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Trend)
                .order_by(desc(Trend.collected_at))
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_unused_trends(self, limit: int = 5) -> list[Trend]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Trend)
                .where(Trend.used_count == 0)
                .order_by(desc(Trend.relevance_score))
                .limit(limit)
            )
            return list(result.scalars().all())

    async def increment_trend_usage(self, trend_id: int):
        async with self.session_factory() as session:
            await session.execute(
                update(Trend)
                .where(Trend.id == trend_id)
                .values(used_count=Trend.used_count + 1)
            )
            await session.commit()

    # ─── Content Queue ─────────────────────────────────────────────

    async def add_to_queue(self, meme_data: dict, priority: float = 0.0) -> ContentQueue:
        async with self.session_factory() as session:
            item = ContentQueue(meme_data=meme_data, priority=priority)
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def get_next_from_queue(self) -> Optional[ContentQueue]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ContentQueue)
                .where(ContentQueue.status == "pending")
                .order_by(desc(ContentQueue.priority))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_queue_size(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(ContentQueue.id))
                .where(ContentQueue.status == "pending")
            )
            return result.scalar() or 0

    async def update_queue_item_status(self, item_id: int, status: str):
        async with self.session_factory() as session:
            await session.execute(
                update(ContentQueue)
                .where(ContentQueue.id == item_id)
                .values(status=status)
            )
            await session.commit()

    async def expire_old_queue_items(self, max_age_hours: int = 48):
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        async with self.session_factory() as session:
            result = await session.execute(
                update(ContentQueue)
                .where(
                    ContentQueue.status == "pending",
                    ContentQueue.created_at < cutoff
                )
                .values(status="expired")
            )
            await session.commit()
            return result.rowcount

    async def clear_queue(self):
        async with self.session_factory() as session:
            await session.execute(
                update(ContentQueue)
                .where(ContentQueue.status == "pending")
                .values(status="expired")
            )
            await session.commit()

    # ─── Strategy Config ───────────────────────────────────────────

    async def get_active_strategy(self) -> Optional[StrategyConfig]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(StrategyConfig)
                .where(StrategyConfig.is_active == True)
                .order_by(desc(StrategyConfig.updated_at))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def save_strategy(self, config_data: dict) -> StrategyConfig:
        async with self.session_factory() as session:
            # Deactivate old strategies
            await session.execute(
                update(StrategyConfig).values(is_active=False)
            )
            strategy = StrategyConfig(config_data=config_data, is_active=True)
            session.add(strategy)
            await session.commit()
            await session.refresh(strategy)
            return strategy

    # ─── System Logs ───────────────────────────────────────────────

    async def save_log(self, level: str, module: str, message: str, details: dict = None):
        async with self.session_factory() as session:
            log = SystemLog(level=level, module=module, message=message, details=details)
            session.add(log)
            await session.commit()

    async def get_recent_logs(self, level: str = None, limit: int = 10) -> list[SystemLog]:
        async with self.session_factory() as session:
            query = select(SystemLog).order_by(desc(SystemLog.timestamp)).limit(limit)
            if level:
                query = query.where(SystemLog.level == level)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_error_count_today(self) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(SystemLog.id))
                .where(
                    SystemLog.level.in_(["ERROR", "CRITICAL"]),
                    SystemLog.timestamp >= today_start
                )
            )
            return result.scalar() or 0

    # ─── API Usage ─────────────────────────────────────────────────

    async def log_api_usage(self, service: str, endpoint: str = None,
                            tokens_used: int = 0, cost: float = 0.0, success: bool = True):
        async with self.session_factory() as session:
            usage = ApiUsage(
                service=service, endpoint=endpoint,
                tokens_used=tokens_used, cost=cost, success=success
            )
            session.add(usage)
            await session.commit()

    async def get_api_usage_today(self, service: str = None) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        async with self.session_factory() as session:
            query = select(
                ApiUsage.service,
                func.count(ApiUsage.id).label("calls"),
                func.sum(ApiUsage.tokens_used).label("total_tokens"),
                func.sum(ApiUsage.cost).label("total_cost")
            ).where(
                ApiUsage.timestamp >= today_start
            ).group_by(ApiUsage.service)

            if service:
                query = query.where(ApiUsage.service == service)

            result = await session.execute(query)
            rows = result.all()
            return {
                row.service: {
                    "calls": row.calls,
                    "total_tokens": row.total_tokens or 0,
                    "total_cost": row.total_cost or 0.0
                }
                for row in rows
            }

    # ─── Stats / Aggregations ─────────────────────────────────────

    async def get_today_stats(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        async with self.session_factory() as session:
            posts = await session.execute(
                select(Post).where(Post.published_at >= today_start)
            )
            posts_list = list(posts.scalars().all())

            total_views = sum(p.views or 0 for p in posts_list)
            total_forwards = sum(p.forwards or 0 for p in posts_list)
            avg_engagement = (
                sum(p.engagement_rate or 0 for p in posts_list) / len(posts_list)
                if posts_list else 0
            )

            return {
                "posts_count": len(posts_list),
                "total_views": total_views,
                "total_forwards": total_forwards,
                "avg_engagement": avg_engagement,
                "avg_views_per_post": total_views // len(posts_list) if posts_list else 0,
            }

    async def get_subscriber_count_change(self) -> int:
        """Placeholder - requires Telegram channel stats API."""
        return 0
