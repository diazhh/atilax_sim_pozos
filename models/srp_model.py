"""SRP (Sucker Rod Pump / Bombeo Mecánico) well model.

Simulates rod loads, dynamometer cards, pump fillage, fluid level,
and SPM with realistic relationships between variables.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from models.well_model import WellModel, LiftType, WellStatus
from utils.units import UnitConverter


@dataclass
class SRPModel(WellModel):
    """SRP (Sucker Rod Pump) well simulation model."""

    # Pumping unit
    unit_type: str = "conventional"
    beam_load_capacity_lb: float = 25000.0
    stroke_length_in: float = 144.0
    max_spm: float = 12.0
    prime_mover_hp: float = 50.0

    # Downhole pump
    pump_bore_in: float = 2.0
    plunger_length_ft: float = 4.0

    # Rod string
    rod_material: str = "grade_D"
    rod_weight_lb_ft: float = 2.2

    # Operating parameters
    spm: float = 7.0
    pump_fillage_pct: float = 85.0
    fluid_level_ft: float = 2500.0
    stroke_counter: int = 0

    # Current state
    current_prl_max_lb: float = 15000.0
    current_prl_min_lb: float = 4000.0

    def __post_init__(self) -> None:
        self.lift_type = LiftType.SRP

    def step(self, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Generate SRP telemetry for one time step."""
        if self.status != WellStatus.PRODUCING:
            return self._shut_in_telemetry(sim_time)

        base = super().step(dt_days, sim_time)
        if not self.reservoir or not self.fluid:
            return base

        flow_rate = base.get("flow_rate_bpd", 0)
        water_cut = base.get("water_cut_pct", 0) / 100.0

        # Pump displacement
        pump_area_sq_in = math.pi * (self.pump_bore_in / 2) ** 2
        displacement_bpd = (
            pump_area_sq_in * self.stroke_length_in * self.spm * 1440 / 9702
        )

        # Fillage based on inflow vs displacement
        if displacement_bpd > 0:
            self.pump_fillage_pct = min(flow_rate / displacement_bpd * 100, 100)
        else:
            self.pump_fillage_pct = 0

        # Fluid level: higher fluid level = lower fillage
        gradient = self.fluid.fluid_gradient(water_cut)
        if gradient > 0:
            self.fluid_level_ft = self.pump_depth_ft - (
                self.reservoir.current_pressure_psi
                - self._noise.gaussian(50, 5.0, min_val=20)
            ) / gradient
            self.fluid_level_ft = max(self.fluid_level_ft, 200)
            self.fluid_level_ft = min(self.fluid_level_ft, self.pump_depth_ft - 100)

        # Rod loads
        rod_weight = self.rod_weight_lb_ft * self.pump_depth_ft
        fluid_load = pump_area_sq_in * gradient * self.fluid_level_ft
        buoyancy = rod_weight * 0.128  # Simplified buoyancy correction

        prl_max = rod_weight + fluid_load - buoyancy
        prl_min = rod_weight - buoyancy - fluid_load * 0.1

        # Dynamic effects (Everitt-Jennings simplified)
        acceleration_factor = 1 + (self.spm / 15) ** 2
        prl_max *= acceleration_factor
        prl_min /= acceleration_factor

        prl_max = max(prl_max, 3000)
        prl_min = max(prl_min, 500)

        # Motor current proportional to load
        avg_load = (prl_max + prl_min) / 2
        load_fraction = avg_load / max(self.beam_load_capacity_lb, 1)
        motor_current = 30 * load_fraction * (self.spm / 7.0)
        motor_power = motor_current * 460 * math.sqrt(3) * 0.8 / 1000  # ~460V 3-phase

        # Wellhead pressure
        thp = self._noise.gaussian(80 - 0.01 * flow_rate, 3.0, min_val=15, max_val=200)
        chp = self._noise.gaussian(150 + 0.02 * flow_rate, 3.0, min_val=30, max_val=400)

        # Stroke counter increment
        strokes_per_step = int(self.spm * dt_days * 1440)
        self.stroke_counter += strokes_per_step

        # Anomaly modifiers
        fillage_mod = self.anomaly_modifiers.get("fillage", 1.0)
        load_mod = self.anomaly_modifiers.get("load", 1.0)

        # Calculate pump efficiency for SRP
        pump_efficiency_pct = min(100, max(30, self.pump_fillage_pct * fillage_mod * 0.9))

        telemetry: dict[str, Any] = {
            "thp_psi": round(thp, 1),
            "chp_psi": round(chp, 1),
            "motor_current_a": round(self._noise.gaussian(motor_current, 5.0, min_val=5), 2),
            "motor_power_kw": round(self._noise.gaussian(motor_power, 3.0, min_val=1), 2),
            "spm": round(self._noise.gaussian(self.spm, 1.0, min_val=2, max_val=15), 2),
            "polished_rod_load_max_lb": round(
                self._noise.gaussian(prl_max * load_mod, 2.0, min_val=2000), 0
            ),
            "polished_rod_load_min_lb": round(
                self._noise.gaussian(prl_min * load_mod, 2.0, min_val=500), 0
            ),
            "fluid_level_ft": round(
                self._noise.gaussian(self.fluid_level_ft, 5.0, min_val=200), 0
            ),
            "pump_fillage_pct": round(
                self._noise.gaussian(
                    self.pump_fillage_pct * fillage_mod, 3.0, min_val=20, max_val=100
                ), 1
            ),
            "pump_efficiency_pct": round(pump_efficiency_pct, 1),
            "stroke_counter": self.stroke_counter,
            "flow_rate_bpd": round(base["flow_rate_bpd"], 1),
            "water_cut_pct": round(base["water_cut_pct"], 2),
        }

        # Add aliases for ThingsBoard rule compatibility
        telemetry["tubing_pressure_psi"] = telemetry["thp_psi"]
        telemetry["casing_pressure_psi"] = telemetry["chp_psi"]
        telemetry["load_lb"] = telemetry["polished_rod_load_max_lb"]

        # Generate dynamo card periodically (~every 30 min sim time)
        minutes_in_step = dt_days * 1440
        if minutes_in_step >= 30 or self._rng.random() < minutes_in_step / 30:
            telemetry["dynamo_card_surface"] = self._generate_dynamo_card(
                prl_max * load_mod, prl_min * load_mod, self.pump_fillage_pct * fillage_mod
            )

        return telemetry

    def _generate_dynamo_card(
        self,
        prl_max: float,
        prl_min: float,
        fillage_pct: float,
    ) -> list[list[float]]:
        """Generate a surface dynamometer card as [[position, load], ...].

        Creates a realistic card shape based on fillage and loads.
        """
        n_points = 200
        card: list[list[float]] = []
        fillage = fillage_pct / 100.0

        for i in range(n_points):
            theta = 2 * math.pi * i / n_points
            # Position: 0 to stroke_length
            position = self.stroke_length_in * (1 - math.cos(theta)) / 2

            if theta < math.pi:
                # Upstroke
                if theta < 0.1 * math.pi:
                    # Loading
                    load = prl_min + (prl_max - prl_min) * (theta / (0.1 * math.pi))
                elif theta < math.pi * fillage:
                    # Full pump — high load
                    load = prl_max
                else:
                    # Gas interference / incomplete fillage
                    blend = (theta - math.pi * fillage) / (math.pi * (1 - fillage))
                    load = prl_max - (prl_max - prl_min) * 0.3 * blend
            else:
                # Downstroke
                if theta < 1.1 * math.pi:
                    # Unloading
                    t = (theta - math.pi) / (0.1 * math.pi)
                    load = prl_max - (prl_max - prl_min) * t
                else:
                    load = prl_min

            # Add noise
            load = self._noise.gaussian(load, 1.0)
            card.append([round(position, 2), round(load, 0)])

        return card

    def get_static_attributes(self) -> dict[str, Any]:
        """SRP-specific server attributes."""
        attrs = super().get_static_attributes()
        attrs.update({
            "srp_unit_type": self.unit_type,
            "srp_beam_load_capacity_lb": self.beam_load_capacity_lb,
            "srp_stroke_length_in": self.stroke_length_in,
            "srp_max_spm": self.max_spm,
            "srp_prime_mover_hp": self.prime_mover_hp,
            "srp_pump_bore_in": self.pump_bore_in,
            "srp_rod_material": self.rod_material,
            "install_date": "",
        })
        return attrs
