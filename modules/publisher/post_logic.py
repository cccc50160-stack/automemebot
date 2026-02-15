"""Publishing pipeline — connects queue, generator, and publisher."""
from datetime import datetime
from modules.database.operations import DatabaseManager
from modules.content_generator.visual_generator import VisualGenerator
from .telegram_publisher import TelegramPublisher


class PostingPipeline:
    def __init__(self, db: DatabaseManager, publisher: TelegramPublisher,
                 visual_gen: VisualGenerator, logger=None):
        self.db = db
        self.publisher = publisher
        self.visual_gen = visual_gen
        self.logger = logger

    async def publish_next(self) -> bool:
        """Take the next meme from queue and publish it. Returns True on success."""
        item = await self.db.get_next_from_queue()
        if not item:
            if self.logger:
                await self.logger.log_warning(
                    "Queue Empty",
                    "No memes in queue to publish."
                )
            return False

        meme = item.meme_data
        meme_type = meme.get("type", "text_only")

        try:
            message_id = None

            if meme_type == "text_only":
                text = meme.get("text", "")
                if not text:
                    await self.db.update_queue_item_status(item.id, "rejected")
                    return False
                message_id = await self.publisher.publish_text(text)
            else:
                # Generate or use existing image
                image_path = meme.get("image_path")
                if not image_path:
                    image_path = await self.visual_gen.generate(meme)

                if image_path:
                    caption = meme.get("caption", "")
                    message_id = await self.publisher.publish_image(image_path, caption)
                else:
                    # Fallback to text if image generation fails
                    fallback_text = self._build_fallback_text(meme)
                    if fallback_text:
                        message_id = await self.publisher.publish_text(fallback_text)

            if message_id:
                # Mark queue item as published
                await self.db.update_queue_item_status(item.id, "published")

                # Save to posts table
                post = await self.db.save_post(
                    telegram_message_id=message_id,
                    content=self._get_content_preview(meme),
                    content_type=meme_type,
                    template_used=meme_type if meme_type != "text_only" else None,
                    trend_topic=meme.get("trend_topic", ""),
                    image_path=meme.get("image_path"),
                    published_at=datetime.utcnow(),
                    quality_score=meme.get("quality_score"),
                    humor_score=meme.get("humor_score"),
                    relevance_score=meme.get("relevance_score"),
                )

                link = self.publisher.get_post_link(message_id)

                if self.logger:
                    await self.logger.log_successful_post({
                        "post_id": post.id,
                        "content_type": meme_type,
                        "preview": self._get_content_preview(meme),
                        "quality_score": meme.get("quality_score", "?"),
                        "relevance_score": meme.get("relevance_score", "?"),
                        "trend_topic": meme.get("trend_topic", "?"),
                        "channel_link": link,
                    })

                return True
            else:
                await self.db.update_queue_item_status(item.id, "rejected")
                return False

        except Exception as e:
            await self.db.update_queue_item_status(item.id, "rejected")
            if self.logger:
                await self.logger.log_error(
                    "Publishing Pipeline Failed",
                    e,
                    {"module": "post_logic", "function": "publish_next"}
                )
            return False

    @staticmethod
    def _get_content_preview(meme: dict) -> str:
        mtype = meme.get("type", "text_only")
        if mtype == "text_only":
            return meme.get("text", "")[:300]
        elif mtype == "drake":
            return f"{meme.get('text_top', '')} / {meme.get('text_bottom', '')}"
        else:
            panels = meme.get("panels", [])
            return " | ".join(panels[:4])

    @staticmethod
    def _build_fallback_text(meme: dict) -> str | None:
        """Build text representation when image generation fails."""
        mtype = meme.get("type", "")
        if mtype == "drake":
            top = meme.get("text_top", "")
            bottom = meme.get("text_bottom", "")
            if top and bottom:
                return f"\u274c {top}\n\u2705 {bottom}"
        elif mtype == "expanding_brain":
            panels = meme.get("panels", [])
            emojis = ["\U0001f9e0", "\U0001f4a1", "\u2728", "\U0001f680"]
            lines = [f"{emojis[i]} {p}" for i, p in enumerate(panels[:4])]
            return "\n".join(lines)
        elif mtype == "two_buttons":
            panels = meme.get("panels", [])
            if len(panels) >= 2:
                return f"\U0001f534 {panels[0]}\n\U0001f535 {panels[1]}\n\n\U0001f630 ..."
        return None
