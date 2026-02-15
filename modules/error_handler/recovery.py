"""Self-recovery logic for the bot."""
import asyncio
from datetime import datetime


class RecoveryManager:
    """Manages automatic recovery from failures."""

    def __init__(self, logger=None):
        self.logger = logger
        self._consecutive_failures: dict[str, int] = {}
        self._recovery_actions: dict[str, callable] = {}
        self._max_failures = 5

    def register_recovery(self, component: str, recovery_func):
        """Register a recovery function for a component."""
        self._recovery_actions[component] = recovery_func

    def record_failure(self, component: str):
        self._consecutive_failures[component] = self._consecutive_failures.get(component, 0) + 1

    def record_success(self, component: str):
        self._consecutive_failures[component] = 0

    def get_failure_count(self, component: str) -> int:
        return self._consecutive_failures.get(component, 0)

    async def attempt_recovery(self, component: str) -> bool:
        """Attempt to recover a failed component."""
        failures = self.get_failure_count(component)

        if failures < self._max_failures:
            return True  # Not critical yet

        if self.logger:
            await self.logger.log_warning(
                "Recovery Triggered",
                f"Component: {component}\n"
                f"Consecutive failures: {failures}\n"
                f"Attempting recovery..."
            )

        recovery_func = self._recovery_actions.get(component)
        if not recovery_func:
            if self.logger:
                await self.logger.log_critical(
                    "No Recovery Available",
                    f"Component: {component}\n"
                    f"No recovery function registered.\n"
                    f"Manual intervention required."
                )
            return False

        try:
            await recovery_func()
            self.record_success(component)
            if self.logger:
                await self.logger.log_info(
                    "Recovery Successful",
                    f"Component: {component} recovered"
                )
            return True
        except Exception as e:
            if self.logger:
                await self.logger.log_critical(
                    "Recovery Failed",
                    f"Component: {component}\n"
                    f"Error: {e}\n"
                    f"Manual intervention required."
                )
            return False

    async def handle_quality_failure(self, generator, consecutive_failures: int):
        """Handle multiple quality filter failures in a row."""
        if consecutive_failures < 5:
            return

        if self.logger:
            await self.logger.log_warning(
                "Multiple Quality Failures",
                f"{consecutive_failures} memes rejected in a row.\n"
                f"Switching to safe mode (proven templates + topics)."
            )

        # Could trigger a strategy change or use reserve content
