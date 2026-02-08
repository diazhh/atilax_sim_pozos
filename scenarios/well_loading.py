"""Well loading / dying well scenario.

Simulates a well gradually loading up (liquid accumulating in
the tubing) until it dies, then potentially recovering after
a shut-in period.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel, WellStatus, LiftType


@dataclass
class WellLoadingScenario:
    """Well loading up (gas well dying / liquid loading).

    Production gradually drops as liquid accumulates in the
    wellbore. THP drops, fluid level rises, and the well
    may eventually die.
    """

    name: str = "well_loading"
    description: str = "Well loading up with liquids, production declining"
    onset_days: float = 30.0
    elapsed_days: float = 0.0
    severity: float = 0.0
    well_died: bool = False
    recovery_time_days: float = 3.0
    _shut_in_elapsed: float = 0.0

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Apply well loading effects."""
        self.elapsed_days += dt_days

        if self.well_died:
            # Well is shut-in, accumulating pressure
            self._shut_in_elapsed += dt_days
            if self._shut_in_elapsed >= self.recovery_time_days:
                # Attempt restart
                self.well_died = False
                self.severity *= 0.3  # Partial recovery
                self.elapsed_days *= 0.3
                well.status = WellStatus.PRODUCING
                return {"well_loading_event": "restart_attempt"}
            else:
                well.status = WellStatus.SHUT_IN
                return {"well_loading_event": "shut_in_recovery"}

        self.severity = min(self.elapsed_days / self.onset_days, 1.0)

        # Production declines
        well.anomaly_modifiers["efficiency"] = max(1.0 - 0.8 * self.severity, 0.05)

        # THP drops as liquid accumulates
        well.anomaly_modifiers["thp_factor"] = max(1.0 - 0.6 * self.severity, 0.2)

        # Check if well dies
        if self.severity > 0.95:
            self.well_died = True
            self._shut_in_elapsed = 0
            well.status = WellStatus.SHUT_IN
            return {
                "well_loading_event": "well_died",
                "loading_severity": self.severity,
            }

        return {
            "loading_severity": self.severity,
            "production_factor": well.anomaly_modifiers.get("efficiency", 1.0),
        }

    def is_applicable(self, well: WellModel) -> bool:
        return well.lift_type in (LiftType.GAS_LIFT, LiftType.ESP)
