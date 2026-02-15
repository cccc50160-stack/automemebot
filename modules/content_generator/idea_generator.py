"""Generate meme ideas using Groq LLM."""
from config.prompts import MEME_GENERATOR_SYSTEM, MEME_GENERATOR_USER
from modules.utils.groq_client import GroqClient


class IdeaGenerator:
    def __init__(self, groq_client: GroqClient, logger=None):
        self.groq = groq_client
        self.logger = logger

    async def generate_ideas(self, trend_topic: str, keywords: list[str],
                             context: str = "", count: int = 5) -> list[dict]:
        """Generate meme ideas based on a trend."""
        user_prompt = MEME_GENERATOR_USER.format(
            trend_topic=trend_topic,
            keywords=", ".join(keywords),
            context=context or trend_topic,
            count=count,
        )

        result = await self.groq.generate(
            system_prompt=MEME_GENERATOR_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.9,
            max_tokens=3000,
        )

        if result is None:
            if self.logger:
                await self.logger.log_error(
                    "Idea Generation Failed",
                    Exception("Groq returned None"),
                    {"module": "idea_generator", "function": "generate_ideas"}
                )
            return []

        # Parse response
        if isinstance(result, dict):
            memes = result.get("memes", [])
        elif isinstance(result, list):
            memes = result
        else:
            if self.logger:
                await self.logger.log_warning(
                    "Unexpected Response Format",
                    f"Expected dict/list, got {type(result).__name__}"
                )
            return []

        # Validate and normalize each meme
        valid_types = {"text_only", "drake", "distracted_bf", "expanding_brain",
                       "two_buttons", "this_is_fine"}
        validated = []
        for meme in memes:
            if not isinstance(meme, dict):
                continue
            meme_type = meme.get("type", "text_only")
            if meme_type not in valid_types:
                meme["type"] = "text_only"
            meme["trend_topic"] = trend_topic
            validated.append(meme)

        if self.logger:
            await self.logger.log_system_event(
                "Ideas Generated",
                f"Trend: {trend_topic}\n"
                f"Generated: {len(validated)} memes\n"
                f"Types: {', '.join(m.get('type', '?') for m in validated)}"
            )

        return validated
