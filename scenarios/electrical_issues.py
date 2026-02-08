"""Electrical issues scenario (typical Venezuela).

Simulates voltage sags, frequency variations, power outages,
and unstable power supply conditions common in Venezuelan
oilfield operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from numpy.random import Generator

from models.well_model import WellModel, WellStatus, LiftType


@dataclass
class ElectricalIssuesScenario:
    """Venezuelan electrical grid instability.

    Simulates:
    - Voltage sags (10-20% drop)
    - Frequency deviations
    - Complete power outages
    - Brownouts and recovery cycles
    """

    name: str = "electrical_issues"
    description: str = "Electrical power instability (Venezuela)"
    outage_prob_per_step: float = 0.05
    sag_prob_per_step: float = 0.15
    sag_magnitude: float = 0.15  # 15% voltage drop
    elapsed_days: float = 0.0
    _in_outage: bool = False
    _outage_remaining_steps: int = 0
    _rng: Generator | None = None

    def apply(self, well: WellModel, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Apply electrical disturbances."""
        if self._rng is None:
            self._rng = np.random.default_rng()

        self.elapsed_days += dt_days
        result: dict[str, Any] = {}

        # Handle ongoing outage
        if self._in_outage:
            self._outage_remaining_steps -= 1
            if self._outage_remaining_steps <= 0:
                self._in_outage = False
                well.status = WellStatus.STARTING
                result["electrical_event"] = "power_restored"
            else:
                well.status = WellStatus.SHUT_IN
                result["electrical_event"] = "outage"
            return result

        # Maybe trigger new outage
        if self._rng.random() < self.outage_prob_per_step:
            self._in_outage = True
            self._outage_remaining_steps = int(self._rng.uniform(2, 20))
            well.status = WellStatus.SHUT_IN
            result["electrical_event"] = "outage_start"
            result["outage_duration_steps"] = self._outage_remaining_steps
            return result

        # Maybe apply voltage sag
        if self._rng.random() < self.sag_prob_per_step:
            sag = self._rng.uniform(0.05, self.sag_magnitude)
            well.anomaly_modifiers["voltage"] = 1.0 - sag
            well.anomaly_modifiers["current"] = 1.0 + sag * 0.5  # Current rises with voltage drop
            result["electrical_event"] = "voltage_sag"
            result["voltage_drop_pct"] = sag * 100
        else:
            # Normal — clear voltage modifiers
            well.anomaly_modifiers.pop("voltage", None)
            well.anomaly_modifiers.pop("current", None)

        return result

    def is_applicable(self, well: WellModel) -> bool:
        return well.lift_type in (LiftType.ESP, LiftType.SRP, LiftType.PCP)
