"""Progress heartbeat — fires every N% completion or on phase change."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.config.settings import HeartbeatConfig

logger = logging.getLogger(__name__)


@dataclass
class HeartbeatState:
    """Tracks the last reported percentage to avoid duplicate heartbeats."""
    last_reported_percent: int = 0
    last_reported_phase: str = ""


class Heartbeat:
    """Progress heartbeat that fires at configured percentage intervals."""

    def __init__(self, config: HeartbeatConfig | None = None):
        self.config = config or HeartbeatConfig()
        self._state = HeartbeatState()

    @property
    def state(self) -> HeartbeatState:
        return self._state

    def check(
        self,
        completed: int,
        total: int,
        current_phase: str = "",
    ) -> Optional[str]:
        """Check if a heartbeat should fire.

        Returns a progress message string if heartbeat fires, None otherwise.
        Fires on:
        - Every N% completion interval
        - Phase change
        """
        if total == 0:
            return None

        current_pct = round(completed / total * 100)

        phase_changed = (
            current_phase
            and current_phase != self._state.last_reported_phase
        )

        interval_hit = (
            current_pct >= self._state.last_reported_percent + self.config.percent_interval
        )

        if phase_changed or interval_hit:
            self._state.last_reported_percent = current_pct
            self._state.last_reported_phase = current_phase

            msg = f"📊 Progress: {completed}/{total} MDUs ({current_pct}%)"
            if current_phase:
                msg += f" | Phase: {current_phase}"

            logger.info(f"[Heartbeat] {msg}")
            return msg

        return None

    def force_report(self, completed: int, total: int, current_phase: str = "") -> str:
        """Force a heartbeat report regardless of interval."""
        current_pct = round(completed / total * 100) if total > 0 else 0
        self._state.last_reported_percent = current_pct
        self._state.last_reported_phase = current_phase

        msg = f"📊 Progress: {completed}/{total} MDUs ({current_pct}%)"
        if current_phase:
            msg += f" | Phase: {current_phase}"
        return msg

    def reset(self) -> None:
        """Reset heartbeat state."""
        self._state = HeartbeatState()
