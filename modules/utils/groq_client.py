"""Async Groq client wrapper with retry logic and usage tracking."""
import asyncio
import json
from groq import AsyncGroq
from config.settings import settings
from modules.utils.helpers import safe_parse_json


class GroqClient:
    def __init__(self, db=None, logger=None):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.db = db
        self.logger = logger
        self._retry_delays = [1, 3, 10]  # seconds

    async def generate(self, system_prompt: str, user_prompt: str,
                       temperature: float = 0.8, max_tokens: int = 2000,
                       parse_json: bool = True) -> dict | str | None:
        """
        Send a request to Groq and return the response.
        If parse_json=True, attempts to parse the response as JSON.
        """
        last_error = None

        for attempt, delay in enumerate(self._retry_delays):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0

                # Track API usage
                if self.db:
                    await self.db.log_api_usage(
                        service="groq",
                        endpoint=self.model,
                        tokens_used=tokens_used,
                        success=True,
                    )

                if parse_json:
                    parsed = safe_parse_json(content)
                    if parsed is not None:
                        return parsed
                    # If parsing failed, return raw content
                    if self.logger:
                        await self.logger.log_warning(
                            "JSON Parse Failed",
                            f"Failed to parse Groq response as JSON.\n"
                            f"Raw response (first 300 chars):\n{content[:300]}"
                        )
                    return content

                return content

            except Exception as e:
                last_error = e
                if self.db:
                    await self.db.log_api_usage(
                        service="groq",
                        endpoint=self.model,
                        tokens_used=0,
                        success=False,
                    )
                if self.logger:
                    await self.logger.log_warning(
                        "Groq API Retry",
                        f"Attempt {attempt + 1}/{len(self._retry_delays)} failed: {e}\n"
                        f"Retrying in {delay}s..."
                    )
                await asyncio.sleep(delay)

        # All retries exhausted
        if self.logger:
            await self.logger.log_error(
                "Groq API Failed",
                last_error,
                {
                    "module": "groq_client",
                    "function": "generate",
                    "traceback": str(last_error),
                }
            )
        return None

    async def check_health(self) -> bool:
        """Quick health check - send a minimal request."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
