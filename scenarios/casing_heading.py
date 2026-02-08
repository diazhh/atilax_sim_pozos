"""Casing heading (slug flow) scenario for gas lift wells.

Simulates pressure oscillations caused by intermittent gas
injection, a common problem in continuous gas lift wells
operating below optimal conditions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel, LiftType
from models.gaslift_model import GasLiftModel


@dataclass
class CasingHeadingScenario:
    """Casing heading oscillations in gas lift wells.

    Produces sinusoidal pressure variations with periods of 5-30 min
    and amplitude increasing with severity.
    """

    name: str = "casing_heading"
    description: str = "Pressure oscillations from unstable gas lift"
    period_min: float = 15.0
    amplitude_psi: float = 120.0
    severity: float = 0.5
    elapsed_days: float = 0.0
    onset_days: float = 2.0

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Apply casing heading to a gas lift well."""
        self.elapsed_days += dt_days
        self.severity = min(self.elapsed_days / self.onset_days, 1.0)

        if isinstance(well, GasLiftModel):
            well.set_casing_heading(
                active=True,
                period_min=self.period_min,
                amplitude_psi=self.amplitude_psi * self.severity,
            )

        return {
            "casing_heading_severity": self.severity,
            "oscillation_period_min": self.period_min,
            "oscillation_amplitude_psi": self.amplitude_psi * self.severity,
        }

    def is_applicable(self, well: WellModel) -> bool:
        return well.lift_type == LiftType.GAS_LIFT
