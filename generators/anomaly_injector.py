"""Anomaly injector for well simulation.

Randomly injects anomalies and failure conditions into wells
with realistic progression patterns. Each anomaly type has
specific signatures that affect correlated telemetry variables.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.random import Generator

from models.well_model import WellModel, LiftType

logger = logging.getLogger(__name__)


@dataclass
class ActiveAnomaly:
    """Tracks an active anomaly on a well."""

    anomaly_type: str
    well_name: str
    start_day: float
    elapsed_days: float = 0.0
    severity: float = 0.0  # 0 to 1, progresses over time
    onset_days: float = 30.0
    resolved: bool = False


class AnomalyInjector:
    """Injects anomalies into well telemetry.

    Supports gradual onset anomalies (degradation, drift) and
    sudden events (gas lock, electrical outage).
    """

    # Anomaly applicability by lift type
    ANOMALY_APPLICABILITY: dict[str, list[str]] = {
        "pump_degradation": ["ESP", "SRP", "PCP"],
        "sensor_drift": ["ESP", "SRP", "gas_lift", "PCP"],
        "gas_interference": ["SRP", "ESP"],
        "electrical_fluctuation": ["ESP", "SRP", "PCP"],
        "water_breakthrough": ["ESP", "SRP", "gas_lift", "PCP"],
        "sand_production": ["PCP", "ESP"],
        "casing_heading": ["gas_lift"],
        "stuck_sensor": ["ESP", "SRP", "gas_lift", "PCP"],
    }

    def __init__(
        self,
        probability_per_well_per_day: float = 0.02,
        enabled_types: list[str] | None = None,
        rng: Generator | None = None,
    ) -> None:
        self.prob_per_day = probability_per_well_per_day
        self.enabled_types = enabled_types or list(self.ANOMALY_APPLICABILITY.keys())
        self.rng = rng or np.random.default_rng()
        self.active_anomalies: dict[str, list[ActiveAnomaly]] = {}  # well_name -> anomalies

    def maybe_inject(self, well: WellModel, dt_days: float) -> None:
        """Potentially inject a new anomaly and update existing ones.

        Called each simulation step for each well.
        """
        well_key = well.name
        if well_key not in self.active_anomalies:
            self.active_anomalies[well_key] = []

        # Update existing anomalies
        self._update_anomalies(well, dt_days)

        # Maybe inject new anomaly
        if self.rng.random() < self.prob_per_day * dt_days:
            self._inject_new(well)

    def _inject_new(self, well: WellModel) -> None:
        """Inject a new anomaly on a well."""
        lift = well.lift_type.value
        applicable = [
            t for t in self.enabled_types
            if lift in self.ANOMALY_APPLICABILITY.get(t, [])
        ]
        if not applicable:
            return

        # Don't stack too many anomalies
        current = self.active_anomalies.get(well.name, [])
        if len(current) >= 2:
            return

        # Don't duplicate same type
        current_types = {a.anomaly_type for a in current}
        candidates = [t for t in applicable if t not in current_types]
        if not candidates:
            return

        anomaly_type = self.rng.choice(candidates)
        onset = self.rng.uniform(10, 60)

        anomaly = ActiveAnomaly(
            anomaly_type=anomaly_type,
            well_name=well.name,
            start_day=well.days_on_production,
            onset_days=onset,
        )
        self.active_anomalies[well.name].append(anomaly)
        logger.info("Injected anomaly '%s' on well %s (onset: %.0f days)", anomaly_type, well.name, onset)

    def _update_anomalies(self, well: WellModel, dt_days: float) -> None:
        """Update severity and apply modifiers for active anomalies."""
        anomalies = self.active_anomalies.get(well.name, [])
        well.anomaly_modifiers.clear()

        to_remove = []
        for anomaly in anomalies:
            anomaly.elapsed_days += dt_days

            # Auto-resolve some anomalies after max duration
            max_duration = anomaly.onset_days * 3
            if anomaly.elapsed_days > max_duration:
                anomaly.resolved = True
                to_remove.append(anomaly)
                continue

            # Calculate severity (0 to 1)
            if anomaly.onset_days > 0:
                anomaly.severity = min(anomaly.elapsed_days / anomaly.onset_days, 1.0)
            else:
                anomaly.severity = 1.0

            # Apply type-specific modifiers
            self._apply_modifiers(well, anomaly)

        for a in to_remove:
            anomalies.remove(a)
            logger.info("Anomaly '%s' resolved on well %s", a.anomaly_type, well.name)

    def _apply_modifiers(self, well: WellModel, anomaly: ActiveAnomaly) -> None:
        """Apply anomaly-specific telemetry modifiers."""
        s = anomaly.severity

        if anomaly.anomaly_type == "pump_degradation":
            well.anomaly_modifiers["efficiency"] = 1.0 - 0.3 * s
            well.anomaly_modifiers["current"] = 1.0 + 0.2 * s
            well.anomaly_modifiers["vibration"] = 1.0 + 0.5 * s
            well.anomaly_modifiers["temperature"] = 1.0 + 0.1 * s

        elif anomaly.anomaly_type == "sensor_drift":
            # One random sensor drifts
            drift_amount = 0.15 * s * self.rng.choice([-1, 1])
            well.anomaly_modifiers["sensor_drift"] = 1.0 + drift_amount

        elif anomaly.anomaly_type == "gas_interference":
            well.anomaly_modifiers["fillage"] = 1.0 - 0.4 * s
            well.anomaly_modifiers["efficiency"] = 1.0 - 0.25 * s

        elif anomaly.anomaly_type == "electrical_fluctuation":
            # Sudden voltage/current fluctuations
            if self.rng.random() < 0.3 * s:
                well.anomaly_modifiers["current"] = self.rng.uniform(0.7, 1.3)
                well.anomaly_modifiers["voltage"] = self.rng.uniform(0.8, 1.1)

        elif anomaly.anomaly_type == "water_breakthrough":
            # Rapid water cut increase
            if well.reservoir:
                wc_increase = 0.001 * s  # Per step
                well.reservoir.water_cut = min(
                    well.reservoir.water_cut + wc_increase, 0.95
                )

        elif anomaly.anomaly_type == "sand_production":
            well.anomaly_modifiers["torque"] = 1.0 + 0.4 * s
            well.anomaly_modifiers["vibration"] = 1.0 + 0.6 * s

        elif anomaly.anomaly_type == "casing_heading":
            from models.gaslift_model import GasLiftModel
            if isinstance(well, GasLiftModel):
                well.set_casing_heading(
                    active=True,
                    period_min=self.rng.uniform(5, 30),
                    amplitude_psi=50 + 150 * s,
                )

        elif anomaly.anomaly_type == "stuck_sensor":
            well.anomaly_modifiers["stuck_sensor"] = 1.0  # Flag for telemetry

    def get_active_count(self) -> int:
        """Total number of active anomalies across all wells."""
        return sum(len(v) for v in self.active_anomalies.values())

    def get_summary(self) -> dict[str, int]:
        """Count anomalies by type."""
        counts: dict[str, int] = {}
        for anomalies in self.active_anomalies.values():
            for a in anomalies:
                counts[a.anomaly_type] = counts.get(a.anomaly_type, 0) + 1
        return counts
