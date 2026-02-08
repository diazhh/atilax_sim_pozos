"""Pump degradation scenario.

Simulates gradual wear of ESP, SRP, or PCP pumps with declining
efficiency, increasing power consumption, and rising vibration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel, LiftType
from models.esp_model import ESPModel
from models.pcp_model import PCPModel


@dataclass
class PumpDegradationScenario:
    """Progressive pump wear leading to reduced efficiency.

    ESP: Efficiency drops, current rises, vibration increases.
    SRP: Fillage drops, loads become erratic.
    PCP: Torque increases, efficiency drops.
    """

    name: str = "pump_degradation"
    description: str = "Gradual pump degradation over weeks/months"
    efficiency_loss_pct_per_day: float = 0.15
    current_rise_pct_per_day: float = 0.10
    vibration_rise_pct_per_day: float = 0.20
    elapsed_days: float = 0.0

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Apply degradation modifiers to the well."""
        self.elapsed_days += dt_days

        eff_factor = max(1.0 - self.efficiency_loss_pct_per_day / 100 * self.elapsed_days, 0.4)
        curr_factor = 1.0 + self.current_rise_pct_per_day / 100 * self.elapsed_days
        vib_factor = 1.0 + self.vibration_rise_pct_per_day / 100 * self.elapsed_days

        well.anomaly_modifiers["efficiency"] = eff_factor
        well.anomaly_modifiers["current"] = min(curr_factor, 1.5)
        well.anomaly_modifiers["vibration"] = min(vib_factor, 3.0)

        if isinstance(well, ESPModel):
            well.pump_efficiency = well.efficiency_at_bep * eff_factor
        elif isinstance(well, PCPModel):
            well.pump_efficiency = 0.70 * eff_factor

        return {
            "degradation_severity": 1 - eff_factor,
            "days_degrading": self.elapsed_days,
        }

    def is_applicable(self, well: WellModel) -> bool:
        return well.lift_type in (LiftType.ESP, LiftType.SRP, LiftType.PCP)
