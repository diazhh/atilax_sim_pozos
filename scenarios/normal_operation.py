"""Normal operation scenario.

Represents a well producing under normal conditions with natural
variability, diurnal cycles, and gradual decline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel


@dataclass
class NormalOperationScenario:
    """Normal steady-state operation with natural variability.

    This is the default scenario. It doesn't add anomalies but
    ensures natural variability through the noise generators
    built into each well model.
    """

    name: str = "normal_operation"
    description: str = "Normal production with natural variability"

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """No-op for normal operation; the well model handles variability."""
        return {}

    def is_applicable(self, well: WellModel) -> bool:
        """Always applicable."""
        return True
