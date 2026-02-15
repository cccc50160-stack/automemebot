"""Content queue manager — ensures queue stays healthy."""
from modules.database.operations import DatabaseManager
from config.settings import settings


class QueueManager:
    def __init__(self, db: DatabaseManager, logger=None):
        self.db = db
        self.logger = logger
        self.min_size = settings.min_queue_size
        self.max_size = settings.max_queue_size

    async def get_size(self) -> int:
        return await self.db.get_queue_size()

    async def needs_refill(self) -> bool:
        size = await self.get_size()
        return size < self.min_size

    async def is_full(self) -> bool:
        size = await self.get_size()
        return size >= self.max_size

    async def add_meme(self, meme_data: dict, priority: float = 0.0) -> bool:
        """Add a meme to queue if not full."""
        if await self.is_full():
            if self.logger:
                await self.logger.log_warning(
                    "Queue Full",
                    f"Queue at max capacity ({self.max_size}). Meme not added."
                )
            return False

        await self.db.add_to_queue(meme_data, priority)
        return True

    async def cleanup_expired(self) -> int:
        """Remove memes older than 48 hours."""
        count = await self.db.expire_old_queue_items(48)
        if count > 0 and self.logger:
            await self.logger.log_system_event(
                "Queue Cleanup",
                f"Expired {count} old memes from queue"
            )
        return count

    async def get_status(self) -> dict:
        size = await self.get_size()
        return {
            "size": size,
            "min": self.min_size,
            "max": self.max_size,
            "needs_refill": size < self.min_size,
            "is_full": size >= self.max_size,
            "health": "ok" if self.min_size <= size <= self.max_size else "warning",
        }
