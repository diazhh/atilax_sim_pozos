"""Gas interference scenario.

Simulates free gas entering the pump, causing erratic behavior
in SRP (incomplete pump fillage, gas-locked dynamo cards) and
ESP (gas lock, surging, reduced head).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel, LiftType


@dataclass
class GasInterferenceScenario:
    """Gas interference affecting pump performance.

    SRP: Irregular fillage, characteristic dynamo card shape.
    ESP: Intermittent gas lock, current and flow fluctuations.
    """

    name: str = "gas_interference"
    description: str = "Free gas entering the pump intake"
    severity: float = 0.0  # 0 to 1
    max_severity: float = 0.8
    onset_days: float = 14.0
    elapsed_days: float = 0.0

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Apply gas interference effects."""
        self.elapsed_days += dt_days
        self.severity = min(self.elapsed_days / self.onset_days, self.max_severity)

        # Erratic fillage/efficiency
        well.anomaly_modifiers["fillage"] = 1.0 - 0.4 * self.severity
        well.anomaly_modifiers["efficiency"] = 1.0 - 0.3 * self.severity

        # Intermittent surging effect
        surge = 0.15 * self.severity * math.sin(self.elapsed_days * 2 * math.pi / 0.5)
        well.anomaly_modifiers["flow_surge"] = 1.0 + surge

        return {
            "gas_interference_severity": self.severity,
        }

    def is_applicable(self, well: WellModel) -> bool:
        return well.lift_type in (LiftType.SRP, LiftType.ESP)
