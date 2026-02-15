"""Trend generation using Groq LLM (primary source when external APIs are unavailable)."""
from datetime import datetime
from config.prompts import TREND_GENERATOR_SYSTEM, TREND_GENERATOR_USER
from modules.utils.groq_client import GroqClient


class GroqTrendCollector:
    def __init__(self, groq_client: GroqClient, logger=None):
        self.groq = groq_client
        self.logger = logger

    async def collect(self, count: int = 10) -> list[dict]:
        """Generate trend suggestions using Groq."""
        user_prompt = TREND_GENERATOR_USER.format(
            count=count,
            date=datetime.now().strftime("%d %B %Y, %A"),
        )

        result = await self.groq.generate(
            system_prompt=TREND_GENERATOR_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.9,
            max_tokens=2000,
        )

        if result is None:
            return []

        if isinstance(result, dict):
            trends = result.get("trends", [])
        elif isinstance(result, list):
            trends = result
        else:
            return []

        # Normalize and validate
        validated = []
        for t in trends:
            if not isinstance(t, dict):
                continue
            validated.append({
                "topic": t.get("topic", "Unknown"),
                "keywords": t.get("keywords", []),
                "context": t.get("context", ""),
                "category": t.get("category", "other"),
                "source": "groq",
                "relevance_score": min(1.0, max(0.0, float(t.get("relevance_score", 0.5)))),
            })

        return validated
