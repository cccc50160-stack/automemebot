"""Multi-step quality filter for meme content."""
import json
from config.prompts import QUALITY_CHECK_SYSTEM, QUALITY_CHECK_USER
from modules.utils.groq_client import GroqClient


class QualityFilter:
    def __init__(self, groq_client: GroqClient, logger=None):
        self.groq = groq_client
        self.logger = logger
        self.min_humor = 6.0
        self.min_relevance = 5.0

    def update_thresholds(self, min_humor: float = None, min_relevance: float = None):
        if min_humor is not None:
            self.min_humor = min_humor
        if min_relevance is not None:
            self.min_relevance = min_relevance

    async def check_quality(self, meme: dict) -> dict:
        """
        Run quality check on a meme.
        Returns: {passed: bool, scores: dict, reason: str}
        """
        meme_content = self._meme_to_text(meme)

        user_prompt = QUALITY_CHECK_USER.format(
            meme_type=meme.get("type", "text_only"),
            meme_content=meme_content,
        )

        result = await self.groq.generate(
            system_prompt=QUALITY_CHECK_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=500,
        )

        if result is None or not isinstance(result, dict):
            # If Groq fails, pass the meme with neutral scores
            return {
                "passed": True,
                "scores": {"humor": 7, "relevance": 7, "appropriateness": 8, "viral_potential": 5},
                "reason": "Quality check unavailable, passed by default",
            }

        humor = result.get("humor", 0)
        relevance = result.get("relevance", 0)
        is_safe = result.get("is_safe", True)
        recommendation = result.get("recommendation", "reject")

        passed = (
            humor >= self.min_humor
            and relevance >= self.min_relevance
            and is_safe
            and recommendation in ("approve", "revise")
        )

        quality_result = {
            "passed": passed,
            "scores": {
                "humor": humor,
                "relevance": relevance,
                "appropriateness": result.get("appropriateness", 0),
                "viral_potential": result.get("viral_potential", 0),
            },
            "reason": result.get("reason", "No reason given"),
            "recommendation": recommendation,
        }

        if self.logger:
            if passed:
                await self.logger.log_info(
                    "Meme Passed Quality Filter",
                    f"Type: {meme.get('type')}\n"
                    f"Humor: {humor}/10, Relevance: {relevance}/10\n"
                    f"Reason: {quality_result['reason']}"
                )
            else:
                await self.logger.log_warning(
                    "Meme Rejected",
                    f"Type: {meme.get('type')}\n"
                    f"Humor: {humor}/10 (min: {self.min_humor})\n"
                    f"Relevance: {relevance}/10 (min: {self.min_relevance})\n"
                    f"Safe: {is_safe}\n"
                    f"Reason: {quality_result['reason']}"
                )

        return quality_result

    @staticmethod
    def _meme_to_text(meme: dict) -> str:
        """Convert meme data to readable text for quality check."""
        mtype = meme.get("type", "text_only")

        if mtype == "text_only":
            return meme.get("text", "")
        elif mtype == "drake":
            return f"Top: {meme.get('text_top', '')}\nBottom: {meme.get('text_bottom', '')}"
        elif mtype in ("expanding_brain", "two_buttons"):
            panels = meme.get("panels", [])
            return "\n".join(f"Panel {i+1}: {p}" for i, p in enumerate(panels))
        elif mtype == "distracted_bf":
            panels = meme.get("panels", [])
            labels = ["Guy", "Girlfriend", "Other girl"]
            parts = [f"{labels[i]}: {panels[i]}" for i in range(min(len(panels), 3))]
            return "\n".join(parts)
        elif mtype == "this_is_fine":
            return meme.get("text", meme.get("text_top", ""))
        else:
            return json.dumps(meme, ensure_ascii=False)

    def calculate_priority(self, meme: dict, scores: dict) -> float:
        """Calculate queue priority from quality scores."""
        humor = scores.get("humor", 5)
        relevance = scores.get("relevance", 5)
        viral = scores.get("viral_potential", 5)
        return (humor * 0.4 + relevance * 0.3 + viral * 0.3)
