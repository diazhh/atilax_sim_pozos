"""Water breakthrough scenario.

Simulates rapid increase in water cut over 2-4 weeks,
with corresponding decline in oil production rate and
changes in fluid properties.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel


@dataclass
class WaterBreakthroughScenario:
    """Rapid water cut increase from water breakthrough.

    Water cut rises from current level to 80-95% over onset period.
    Oil production drops correspondingly.
    """

    name: str = "water_breakthrough"
    description: str = "Sudden water breakthrough from aquifer or nearby injector"
    target_water_cut: float = 0.90
    onset_days: float = 21.0
    elapsed_days: float = 0.0
    initial_water_cut: float | None = None

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Progressively increase water cut."""
        if not well.reservoir:
            return {}

        if self.initial_water_cut is None:
            self.initial_water_cut = well.reservoir.water_cut

        self.elapsed_days += dt_days
        progress = min(self.elapsed_days / self.onset_days, 1.0)

        # S-curve progression (logistic-like)
        s_curve = progress ** 2 * (3 - 2 * progress)

        new_wc = self.initial_water_cut + (
            self.target_water_cut - self.initial_water_cut
        ) * s_curve

        well.reservoir.water_cut = min(new_wc, 0.98)

        return {
            "water_breakthrough_progress": progress,
            "water_cut_pct": well.reservoir.water_cut * 100,
        }

    def is_applicable(self, well: WellModel) -> bool:
        return True
