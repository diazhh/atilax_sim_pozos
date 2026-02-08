"""Base well model with common attributes and state.

Serves as the foundation for all lift-type-specific models.
Contains well geometry, completion data, and orchestrates the
reservoir + fluid + lift system interaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from numpy.random import Generator

from models.reservoir_model import ReservoirModel
from models.fluid_model import FluidModel
from utils.noise import NoiseGenerator


class LiftType(str, Enum):
    ESP = "ESP"
    SRP = "SRP"
    GAS_LIFT = "gas_lift"
    PCP = "PCP"


class WellStatus(str, Enum):
    PRODUCING = "producing"
    SHUT_IN = "shut_in"
    WORKOVER = "workover"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class WellModel:
    """Base well model with geometry, reservoir, and fluid.

    Attributes:
        name: Well identifier (e.g., "LM-EST01-003").
        field_name: Parent field name.
        macolla_name: Parent macolla name.
        lift_type: Artificial lift method.
        status: Current operating status.
        reservoir: Reservoir inflow model.
        fluid: PVT fluid model.
    """

    # Identity
    name: str
    field_name: str
    macolla_name: str
    lift_type: LiftType

    # State
    status: WellStatus = WellStatus.PRODUCING

    # Sub-models (set during initialization)
    reservoir: ReservoirModel | None = None
    fluid: FluidModel | None = None

    # Well geometry
    total_depth_md_ft: float = 8000.0
    total_depth_tvd_ft: float = 7500.0
    casing_od_in: float = 7.0
    casing_id_in: float = 6.184
    tubing_od_in: float = 2.875
    tubing_id_in: float = 2.441
    pump_depth_ft: float = 6000.0
    perforations_top_ft: float = 7000.0
    perforations_bottom_ft: float = 7500.0
    completion_type: str = "vertical"
    deviation_survey: list[dict[str, float]] = field(default_factory=list)

    # Production tracking
    cumulative_oil_stb: float = 0.0
    cumulative_water_stb: float = 0.0
    cumulative_gas_mscf: float = 0.0
    days_on_production: float = 0.0

    # Anomaly state
    active_anomalies: list[dict[str, Any]] = field(default_factory=list)
    anomaly_modifiers: dict[str, float] = field(default_factory=dict)

    # Internal
    _rng: Generator = field(default_factory=lambda: np.random.default_rng())
    _noise: NoiseGenerator = field(default_factory=NoiseGenerator)

    def set_rng(self, rng: Generator) -> None:
        self._rng = rng
        self._noise = NoiseGenerator(rng)
        if self.reservoir:
            self.reservoir.set_rng(rng)

    def calculate_pwf(self) -> float:
        """Calculate flowing bottom-hole pressure.

        Simplified: Pwf = Pdischarge (at pump) + hydrostatic below pump
        Subclasses override for lift-specific calculation.
        """
        if not self.fluid:
            return 500.0
        wc = self.reservoir.water_cut if self.reservoir else 0.3
        gradient = self.fluid.fluid_gradient(wc)
        depth_below_pump = self.perforations_top_ft - self.pump_depth_ft
        return max(gradient * depth_below_pump + 50, 50.0)

    def step(self, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Advance well simulation by dt_days.

        This is the base implementation; lift-specific models override
        to add their telemetry.

        Args:
            dt_days: Simulation time step (days).
            sim_time: Current simulation datetime.

        Returns:
            Telemetry dict with all sensor readings.
        """
        if self.status != WellStatus.PRODUCING:
            return self._shut_in_telemetry(sim_time)

        if not self.reservoir:
            return {}

        pwf = self.calculate_pwf()
        res_state = self.reservoir.step(pwf, dt_days)

        self.days_on_production += dt_days
        self.cumulative_oil_stb += res_state["oil_rate_bpd"] * dt_days
        self.cumulative_water_stb += res_state["water_rate_bpd"] * dt_days
        self.cumulative_gas_mscf += (
            res_state["gor_scf_stb"] * res_state["oil_rate_bpd"] * dt_days / 1000
        )

        telemetry: dict[str, Any] = {
            "flow_rate_bpd": self._noise.with_outliers(
                res_state["flow_rate_bpd"], noise_pct=7.0, min_val=0
            ),
            "water_cut_pct": self._noise.gaussian(
                res_state["water_cut_pct"], noise_pct=3.0, min_val=0, max_val=100
            ),
            "gor_scf_stb": self._noise.gaussian(
                res_state["gor_scf_stb"], noise_pct=5.0, min_val=0
            ),
        }

        # Apply anomaly modifiers
        for key, modifier in self.anomaly_modifiers.items():
            if key in telemetry:
                telemetry[key] *= modifier

        return telemetry

    def _shut_in_telemetry(self, sim_time: datetime) -> dict[str, Any]:
        """Telemetry when well is shut in."""
        return {
            "flow_rate_bpd": 0.0,
            "water_cut_pct": 0.0,
            "gor_scf_stb": 0.0,
            "thp_psi": self._noise.gaussian(
                self.reservoir.current_pressure_psi * 0.3 if self.reservoir else 100,
                noise_pct=1.0,
            ),
        }

    def apply_anomaly(self, anomaly: dict[str, Any]) -> None:
        """Register an active anomaly on this well."""
        self.active_anomalies.append(anomaly)

    def clear_anomaly(self, anomaly_type: str) -> None:
        """Remove an anomaly by type."""
        self.active_anomalies = [
            a for a in self.active_anomalies if a.get("type") != anomaly_type
        ]
        # Remove related modifiers
        keys_to_remove = [k for k in self.anomaly_modifiers if k.startswith(anomaly_type)]
        for k in keys_to_remove:
            del self.anomaly_modifiers[k]

    def get_static_attributes(self) -> dict[str, Any]:
        """Return all server attributes for ThingsBoard entity creation."""
        attrs: dict[str, Any] = {
            # Well identity
            "well_name": self.name,
            "well_code_pdvsa": f"PDVSA-{self.field_name[:3].upper()}-{self.name}",
            "field_name": self.field_name,
            "macolla_name": self.macolla_name,
            "lift_type": self.lift_type.value,
            "lifting_type": self.lift_type.value,
            "status": self.status.value,
            # Geometry
            "total_depth_md_ft": self.total_depth_md_ft,
            "total_depth_tvd_ft": self.total_depth_tvd_ft,
            "casing_od_in": self.casing_od_in,
            "casing_id_in": self.casing_id_in,
            "tubing_od_in": self.tubing_od_in,
            "tubing_id_in": self.tubing_id_in,
            "pump_depth_ft": self.pump_depth_ft,
            "perforations_top_ft": self.perforations_top_ft,
            "perforations_bottom_ft": self.perforations_bottom_ft,
            "completion_type": self.completion_type,
            # Optimization placeholders
            "opt_last_run": "",
            "opt_current_operating_point_bpd": 0,
            "opt_recommended_rate_bpd": 0,
            "opt_potential_gain_bpd": 0,
            "opt_potential_gain_percent": 0,
            "opt_recommended_action": "",
            "opt_efficiency_percent": 0,
            "opt_specific_energy_kwh_bbl": 0,
            "opt_well_health_score": 0,
            "opt_status": "",
            "opt_decline_rate_monthly_percent": 0,
            "opt_cluster_id": "",
            "opt_similar_wells": "",
        }

        # Add reservoir attributes
        if self.reservoir:
            attrs.update(self.reservoir.get_attributes())

        return attrs

    def get_device_type(self) -> str:
        """Return the ThingsBoard device type for the RTU."""
        mapping = {
            LiftType.ESP: "rtu_esp",
            LiftType.SRP: "rtu_srp",
            LiftType.GAS_LIFT: "rtu_gaslift",
            LiftType.PCP: "rtu_pcp",
        }
        return mapping[self.lift_type]
