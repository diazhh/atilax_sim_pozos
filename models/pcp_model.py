"""PCP (Progressive Cavity Pump) well model.

Simulates torque, RPM, motor loading, and sand production
for wells with progressing cavity pumps, typical in the
Faja Petrolifera del Orinoco with extra-heavy crude.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.well_model import WellModel, LiftType, WellStatus
from utils.units import UnitConverter


@dataclass
class PCPModel(WellModel):
    """PCP (Progressive Cavity Pump) well simulation model."""

    # Pump parameters
    pump_model: str = "Moyno 7L6"
    pump_geometry: str = "2-3 lobe"
    pump_stages: int = 3
    displacement_cc_rev: float = 1200.0
    max_rate_bpd: float = 2000.0
    max_differential_psi: float = 2000.0
    elastomer_type: str = "NBR"
    elastomer_temp_max_f: float = 275.0
    design_temperature_f: float = 200.0

    # Drive parameters
    drive_type: str = "surface_drive"
    max_rpm: float = 400.0
    max_torque_ftlb: float = 4500.0
    motor_hp: float = 60.0
    motor_voltage_v: float = 460.0
    gear_ratio: float = 14.7
    has_vsd: bool = True
    brake_type: str = "band"

    # Rod string
    rod_type: str = "continuous"
    rod_diameter_in: float = 1.0
    rod_grade: str = "D"
    rod_coupling_type: str = "slim_hole"

    # Fluid composition (well-specific)
    h2s_ppm: float = 0.0
    co2_pct: float = 0.0

    # Operating state
    drive_rpm: float = 250.0
    current_torque_ftlb: float = 2000.0
    sand_pct: float = 1.0
    pump_efficiency: float = 0.70

    def __post_init__(self) -> None:
        self.lift_type = LiftType.PCP

    def step(self, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Generate PCP telemetry for one time step."""
        if self.status != WellStatus.PRODUCING:
            return self._shut_in_telemetry(sim_time)

        base = super().step(dt_days, sim_time)
        if not self.reservoir or not self.fluid:
            return base

        flow_rate = base.get("flow_rate_bpd", 0)
        water_cut = base.get("water_cut_pct", 0) / 100.0

        # PCP displacement proportional to RPM
        displacement_per_rev_bbl = self.max_rate_bpd / (self.max_rpm * 1440)
        actual_displacement_bpd = (
            displacement_per_rev_bbl * self.drive_rpm * 1440 * self.pump_efficiency
        )

        # Torque: function of differential pressure and pump geometry
        gradient = self.fluid.fluid_gradient(water_cut)
        viscosity = self.fluid.live_oil_viscosity(
            self.reservoir.current_pressure_psi
        ) if self.fluid else 1000

        # Higher viscosity = higher torque
        viscosity_factor = 1 + 0.0001 * min(viscosity, 10000)

        # Differential pressure across pump
        dp_psi = gradient * (self.pump_depth_ft - 200)  # Simplified
        dp_psi = min(dp_psi, self.max_differential_psi)

        # Torque model: T ∝ ΔP × geometry × viscosity
        base_torque = dp_psi * 0.8 * viscosity_factor
        torque = min(base_torque, self.max_torque_ftlb)

        # Sand adds friction torque
        sand_torque = self.sand_pct * 100  # ~100 ft-lb per % sand
        torque += sand_torque

        # Motor electrical
        mechanical_power_hp = torque * self.drive_rpm / 5252
        motor_load_fraction = mechanical_power_hp / max(self.motor_hp, 1)
        motor_current = 35 * motor_load_fraction  # Simplified
        motor_power_kw = UnitConverter.hp_to_kw(mechanical_power_hp) / 0.9  # Motor efficiency

        # Intake pressure if sensor installed (50% chance modeled)
        intake_p = self.reservoir.current_pressure_psi - gradient * (
            self.perforations_top_ft - self.pump_depth_ft
        )
        intake_p = max(intake_p, 30)

        # Wellhead pressures
        thp = self._noise.gaussian(
            100 - 0.02 * flow_rate + 20 * (1 - water_cut),
            2.0, min_val=15, max_val=300
        )
        chp = self._noise.gaussian(
            200 + 0.01 * flow_rate,
            2.0, min_val=30, max_val=500
        )

        # Anomaly modifiers
        torque_mod = self.anomaly_modifiers.get("torque", 1.0)
        efficiency_mod = self.anomaly_modifiers.get("efficiency", 1.0)

        # Calculate pump efficiency for PCP
        volumetric_efficiency = min(100, max(40, 95 * efficiency_mod))
        pump_efficiency_pct = volumetric_efficiency * 0.85

        telemetry: dict[str, Any] = {
            "thp_psi": round(thp, 1),
            "chp_psi": round(chp, 1),
            "drive_torque_ftlb": round(
                self._noise.gaussian(torque * torque_mod, 5.0, min_val=100), 1
            ),
            "drive_rpm": round(
                self._noise.gaussian(self.drive_rpm, 1.5, min_val=30), 1
            ),
            "motor_current_a": round(
                self._noise.gaussian(motor_current, 4.0, min_val=5), 2
            ),
            "motor_power_kw": round(
                self._noise.gaussian(motor_power_kw, 3.0, min_val=1), 2
            ),
            "intake_pressure_psi": round(
                self._noise.gaussian(intake_p, 2.0, min_val=30), 1
            ),
            "flow_rate_bpd": round(base["flow_rate_bpd"] * efficiency_mod, 1),
            "water_cut_pct": round(base["water_cut_pct"], 2),
            "sand_pct": round(
                self._noise.with_outliers(self.sand_pct, 25.0, min_val=0, max_val=10), 2
            ),
            "pump_efficiency_pct": round(self._noise.gaussian(pump_efficiency_pct, 1.5, min_val=30, max_val=100), 1),
        }

        # Add aliases for ThingsBoard rule compatibility
        telemetry["tubing_pressure_psi"] = telemetry["thp_psi"]
        telemetry["casing_pressure_psi"] = telemetry["chp_psi"]
        telemetry["speed_rpm"] = telemetry["drive_rpm"]
        telemetry["motor_torque_ftlb"] = telemetry["drive_torque_ftlb"]

        return telemetry

    def get_static_attributes(self) -> dict[str, Any]:
        """PCP-specific server attributes."""
        attrs = super().get_static_attributes()
        attrs.update({
            # Pump
            "pcp_pump_model": self.pump_model,
            "pcp_pump_geometry": self.pump_geometry,
            "pcp_pump_stages": self.pump_stages,
            "pcp_displacement_cc_rev": self.displacement_cc_rev,
            "pcp_max_rate_bpd": self.max_rate_bpd,
            "pcp_max_differential_psi": self.max_differential_psi,
            "pcp_elastomer_type": self.elastomer_type,
            "pcp_elastomer_temp_max_f": self.elastomer_temp_max_f,
            "pcp_design_temperature_f": self.design_temperature_f,
            # Drive / Motor
            "pcp_drive_type": self.drive_type,
            "pcp_max_rpm": self.max_rpm,
            "pcp_max_torque_ftlb": self.max_torque_ftlb,
            "pcp_motor_hp": self.motor_hp,
            "pcp_motor_voltage_v": self.motor_voltage_v,
            "pcp_gear_ratio": self.gear_ratio,
            "pcp_has_vsd": self.has_vsd,
            "pcp_brake_type": self.brake_type,
            # Rod string
            "pcp_rod_type": self.rod_type,
            "pcp_rod_diameter_in": self.rod_diameter_in,
            "pcp_rod_grade": self.rod_grade,
            "pcp_rod_coupling_type": self.rod_coupling_type,
            # Fluid composition
            "pcp_h2s_ppm": self.h2s_ppm,
            "pcp_co2_pct": self.co2_pct,
            "pcp_sand_pct_initial": self.sand_pct,
            "install_date": "",
        })
        return attrs
