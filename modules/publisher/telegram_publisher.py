"""Telegram channel publisher with retry logic."""
import asyncio
from pathlib import Path
from telegram import Bot
from telegram.error import TelegramError
from config.settings import settings


class TelegramPublisher:
    def __init__(self, logger=None):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.channel_id = settings.telegram_channel_id
        self.channel_username = settings.telegram_channel_username
        self.logger = logger
        self._max_retries = 3

    async def publish_text(self, text: str) -> int | None:
        """Publish a text-only meme. Returns message_id or None."""
        return await self._retry(self._send_text, text)

    async def publish_image(self, image_path: str, caption: str = "") -> int | None:
        """Publish an image meme with caption. Returns message_id or None."""
        return await self._retry(self._send_image, image_path, caption)

    async def _send_text(self, text: str) -> int:
        msg = await self.bot.send_message(
            chat_id=self.channel_id,
            text=text,
            parse_mode="HTML",
        )
        return msg.message_id

    async def _send_image(self, image_path: str, caption: str) -> int:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(path, "rb") as f:
            msg = await self.bot.send_photo(
                chat_id=self.channel_id,
                photo=f,
                caption=caption or None,
                parse_mode="HTML" if caption else None,
            )
        return msg.message_id

    async def _retry(self, func, *args) -> int | None:
        """Execute with exponential backoff retry."""
        for attempt in range(self._max_retries):
            try:
                result = await func(*args)
                return result
            except TelegramError as e:
                if attempt == self._max_retries - 1:
                    if self.logger:
                        await self.logger.log_error(
                            "Publishing Failed",
                            e,
                            {
                                "module": "telegram_publisher",
                                "function": func.__name__,
                                "attempts": self._max_retries,
                            }
                        )
                    return None

                delay = 2 ** attempt
                if self.logger:
                    await self.logger.log_warning(
                        f"Publish Attempt {attempt + 1} Failed",
                        f"Error: {e}\nRetry in {delay}s..."
                    )
                await asyncio.sleep(delay)

        return None

    def get_post_link(self, message_id: int) -> str:
        """Generate a link to a published post."""
        username = self.channel_username.lstrip("@")
        return f"https://t.me/{username}/{message_id}"

    async def get_chat_member_count(self) -> int:
        """Get current subscriber count."""
        try:
            count = await self.bot.get_chat_member_count(self.channel_id)
            return count
        except TelegramError:
            return 0

    async def check_health(self) -> bool:
        """Check if the bot can reach Telegram."""
        try:
            me = await self.bot.get_me()
            return me is not None
        except Exception:
            return False
