"""Circuit breaker for task decomposition — depth limit, MDU cap, sub-item cap."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.config.settings import CircuitBreakerConfig

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Tracks circuit breaker counters during decomposition."""
    current_depth: int = 0
    total_mdu_count: int = 0
    tripped: bool = False
    trip_reason: str = ""


class CircuitBreaker:
    """Enforces decomposition limits to prevent infinite recursion and over-scoping."""

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()

    @property
    def state(self) -> CircuitBreakerState:
        return self._state

    def check_depth(self, depth: int) -> bool:
        """Check if depth limit is exceeded. Returns True if OK, False if tripped."""
        self._state.current_depth = depth
        if depth > self.config.max_depth:
            self._trip(
                f"Depth limit exceeded: {depth} > {self.config.max_depth}. "
                f"Mark current items as MDUs even if imperfect."
            )
            return False
        return True

    def check_mdu_count(self, count: int) -> bool:
        """Check if MDU count limit is exceeded. Returns True if OK, False if tripped."""
        self._state.total_mdu_count = count
        if count >= self.config.max_mdu_count:
            self._trip(
                f"MDU count limit reached: {count} >= {self.config.max_mdu_count}. "
                f"Stop decomposing immediately."
            )
            return False
        return True

    def check_sub_items(self, sub_count: int, task_name: str = "") -> bool:
        """Check if sub-item count limit is exceeded. Returns True if OK, False if tripped."""
        if sub_count > self.config.max_sub_items:
            self._trip(
                f"Sub-item limit exceeded for '{task_name}': "
                f"{sub_count} > {self.config.max_sub_items}. "
                f"Merge related items to reduce count."
            )
            return False
        return True

    def check_all(self, depth: int, mdu_count: int, sub_count: int, task_name: str = "") -> bool:
        """Run all checks. Returns True if all pass."""
        d = self.check_depth(depth)
        m = self.check_mdu_count(mdu_count)
        s = self.check_sub_items(sub_count, task_name)
        return d and m and s

    def reset(self) -> None:
        """Reset circuit breaker state."""
        self._state = CircuitBreakerState()

    def _trip(self, reason: str) -> None:
        """Trip the circuit breaker."""
        self._state.tripped = True
        self._state.trip_reason = reason
        logger.warning(f"[CircuitBreaker] TRIPPED: {reason}")
