"""Self-learning algorithm that adjusts strategy based on post performance."""
import json
from config.prompts import STRATEGY_ANALYSIS_SYSTEM, STRATEGY_ANALYSIS_USER
from modules.database.operations import DatabaseManager
from modules.utils.groq_client import GroqClient
from modules.utils.helpers import DEFAULT_STRATEGY
from .metrics_collector import MetricsCollector


class LearningAlgorithm:
    def __init__(self, db: DatabaseManager, groq_client: GroqClient,
                 metrics: MetricsCollector, logger=None):
        self.db = db
        self.groq = groq_client
        self.metrics = metrics
        self.logger = logger

    async def get_current_strategy(self) -> dict:
        """Get the currently active strategy, or return default."""
        strategy = await self.db.get_active_strategy()
        if strategy and strategy.config_data:
            return strategy.config_data
        return dict(DEFAULT_STRATEGY)

    async def analyze_and_update(self) -> dict | None:
        """Analyze recent performance and suggest strategy updates."""
        current = await self.get_current_strategy()
        avg_metrics = await self.metrics.get_average_metrics(days=7)
        type_stats = await self.metrics.get_best_content_types(days=14)

        if avg_metrics["total_posts"] < 5:
            # Not enough data to optimize
            return None

        # Build metrics summary for Groq analysis
        metrics_summary = json.dumps({
            "average_7d": avg_metrics,
            "content_type_performance": type_stats,
        }, indent=2, ensure_ascii=False)

        user_prompt = STRATEGY_ANALYSIS_USER.format(
            period="7 days",
            current_strategy=json.dumps(current, indent=2, ensure_ascii=False),
            metrics_summary=metrics_summary,
        )

        result = await self.groq.generate(
            system_prompt=STRATEGY_ANALYSIS_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.4,
            max_tokens=1500,
        )

        if not result or not isinstance(result, dict):
            return None

        # Apply recommendations with conservative blending
        new_strategy = dict(current)
        recommendations = result.get("recommendations", [])

        for rec in recommendations:
            param = rec.get("parameter", "")
            suggested = rec.get("suggested_value")
            if not param or suggested is None:
                continue

            # Apply with 70/30 blend (conservative)
            if param in new_strategy and isinstance(new_strategy[param], dict) and isinstance(suggested, dict):
                for key in suggested:
                    if key in new_strategy[param]:
                        old_val = new_strategy[param][key]
                        new_val = suggested[key]
                        if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                            new_strategy[param][key] = round(old_val * 0.7 + new_val * 0.3, 3)
                        else:
                            new_strategy[param][key] = new_val

        # Save new strategy
        await self.db.save_strategy(new_strategy)

        # Log the update
        if self.logger:
            reason = result.get("content_insights", "Periodic optimization")
            await self.logger.log_strategy_update(current, new_strategy, reason)

        return new_strategy

    async def ensure_strategy_exists(self):
        """Make sure a strategy exists in the database."""
        strategy = await self.db.get_active_strategy()
        if not strategy:
            await self.db.save_strategy(DEFAULT_STRATEGY)
