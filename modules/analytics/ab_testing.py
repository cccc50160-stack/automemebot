"""Simple A/B testing framework for content optimization."""
import random
from datetime import datetime, timedelta
from modules.database.operations import DatabaseManager


class ABTestManager:
    def __init__(self, db: DatabaseManager, logger=None):
        self.db = db
        self.logger = logger
        self._active_tests: dict[str, dict] = {}

    def create_test(self, test_name: str, variant_a: dict, variant_b: dict,
                    duration_days: int = 7, sample_size: int = 20):
        """Create a new A/B test."""
        self._active_tests[test_name] = {
            "test_name": test_name,
            "variant_a": {**variant_a, "posts": [], "metrics": []},
            "variant_b": {**variant_b, "posts": [], "metrics": []},
            "created_at": datetime.utcnow(),
            "duration_days": duration_days,
            "target_sample": sample_size,
            "status": "active",
        }

    def get_variant(self, test_name: str) -> str:
        """Get which variant to use (returns 'a' or 'b')."""
        test = self._active_tests.get(test_name)
        if not test or test["status"] != "active":
            return "a"
        # Simple random assignment
        return random.choice(["a", "b"])

    def record_result(self, test_name: str, variant: str, post_id: int,
                      views: int = 0, engagement: float = 0.0):
        """Record a result for a test variant."""
        test = self._active_tests.get(test_name)
        if not test:
            return

        key = f"variant_{variant}"
        test[key]["posts"].append(post_id)
        test[key]["metrics"].append({
            "views": views,
            "engagement": engagement,
        })

        # Check if test is complete
        total_samples = len(test["variant_a"]["posts"]) + len(test["variant_b"]["posts"])
        if total_samples >= test["target_sample"]:
            test["status"] = "completed"

    async def evaluate_test(self, test_name: str) -> dict | None:
        """Evaluate a completed test and determine the winner."""
        test = self._active_tests.get(test_name)
        if not test:
            return None

        va = test["variant_a"]
        vb = test["variant_b"]

        if not va["metrics"] or not vb["metrics"]:
            return None

        avg_views_a = sum(m["views"] for m in va["metrics"]) / len(va["metrics"])
        avg_views_b = sum(m["views"] for m in vb["metrics"]) / len(vb["metrics"])
        avg_eng_a = sum(m["engagement"] for m in va["metrics"]) / len(va["metrics"])
        avg_eng_b = sum(m["engagement"] for m in vb["metrics"]) / len(vb["metrics"])

        # Simple comparison (no statistical significance for now)
        winner = "A" if avg_eng_a >= avg_eng_b else "B"
        difference = abs(avg_eng_a - avg_eng_b) / max(avg_eng_a, avg_eng_b, 0.001) * 100

        result = {
            "test_name": test_name,
            "duration": f"{test['duration_days']} days",
            "sample_size": len(va["posts"]) + len(vb["posts"]),
            "variant_a": {
                "description": va.get("description", "Variant A"),
                "avg_views": int(avg_views_a),
                "engagement": avg_eng_a,
            },
            "variant_b": {
                "description": vb.get("description", "Variant B"),
                "avg_views": int(avg_views_b),
                "engagement": avg_eng_b,
            },
            "winner": f"Variant {winner}",
            "difference": difference,
            "recommendation": f"Use Variant {winner} strategy",
        }

        if self.logger:
            await self.logger.log_ab_test_results(result)

        # Clean up
        del self._active_tests[test_name]

        return result

    def get_active_tests(self) -> list[str]:
        return [name for name, t in self._active_tests.items() if t["status"] == "active"]
