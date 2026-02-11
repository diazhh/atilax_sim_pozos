"""Gas Lift well model.

Simulates continuous gas lift with injection rate optimization,
gas lift performance curve (GLPC), choke control, and casing
heading oscillations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from models.well_model import WellModel, LiftType, WellStatus


@dataclass
class GasLiftModel(WellModel):
    """Gas Lift well simulation model."""

    # Mandrel/Valve configuration
    num_mandrels: int = 5
    operating_valve_depth_ft: float = 7000.0
    valve_port_size_64ths: int = 16
    valve_type: str = "IPO"
    valve_depths_ft: list[float] = field(default_factory=lambda: [2000, 3500, 5000, 6000, 7000])
    valve_opening_psi: list[float] = field(default_factory=lambda: [1200, 1100, 1000, 950, 900])
    valve_closing_psi: list[float] = field(default_factory=lambda: [1050, 960, 870, 820, 780])
    annular_volume_bbl: float = 120.0

    # Injection parameters
    injection_rate_mscfd: float = 600.0
    injection_pressure_psi: float = 1200.0
    optimal_injection_mscfd: float = 500.0
    max_injection_mscfd: float = 1200.0
    design_injection_mscfd: float = 800.0

    # Gas supply infrastructure
    gas_supply_pressure_psi: float = 1300.0
    gas_max_available_mscfd: float = 1200.0
    gas_cost_usd_mscf: float = 2.50

    # Choke
    choke_size_64ths: int = 24

    # Casing heading state
    _heading_active: bool = False
    _heading_phase: float = 0.0
    _heading_period_min: float = 15.0
    _heading_amplitude_psi: float = 100.0

    def __post_init__(self) -> None:
        self.lift_type = LiftType.GAS_LIFT

    def step(self, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Generate gas lift telemetry for one time step."""
        if self.status != WellStatus.PRODUCING:
            return self._shut_in_telemetry(sim_time)

        base = super().step(dt_days, sim_time)
        if not self.reservoir or not self.fluid:
            return base

        flow_rate = base.get("flow_rate_bpd", 0)
        water_cut = base.get("water_cut_pct", 0) / 100.0

        # GLPC effect: production response to injection rate
        glpc_factor = self._glpc_factor(self.injection_rate_mscfd)
        effective_flow = flow_rate * glpc_factor

        # Pressures
        gradient = self.fluid.fluid_gradient(water_cut)
        # THP affected by choke and injection
        thp = self._noise.gaussian(
            200 - 0.05 * effective_flow + 0.1 * self.injection_pressure_psi * 0.1,
            3.0, min_val=50, max_val=500
        )

        # Casing head pressure = injection pressure minus losses
        chp_base = self.injection_pressure_psi * 0.85

        # Apply casing heading oscillation if active
        if self._heading_active:
            minutes = sim_time.hour * 60 + sim_time.minute + sim_time.second / 60.0
            self._heading_phase = 2 * math.pi * minutes / self._heading_period_min
            heading_offset = self._heading_amplitude_psi * math.sin(self._heading_phase)
            chp_base += heading_offset
            # Production also oscillates
            effective_flow *= (1 + 0.15 * math.sin(self._heading_phase))

        chp = self._noise.gaussian(chp_base, 3.0, min_val=100)

        # Wellhead temperature
        hour = sim_time.hour + sim_time.minute / 60.0
        diurnal = self._noise.diurnal_factor(hour, 0.015)
        tht = self._noise.gaussian(
            self.reservoir.temperature_f * 0.55 * diurnal, 0.8, min_val=80
        )

        # Total GOR = formation GOR + injected GLR
        formation_gor = base.get("gor_scf_stb", 200)
        oil_rate = effective_flow * (1 - water_cut)
        injected_glr = self.injection_rate_mscfd * 1000 / max(oil_rate, 1)
        total_gor = formation_gor + injected_glr

        telemetry: dict[str, Any] = {
            "thp_psi": round(thp, 1),
            "chp_psi": round(chp, 1),
            "tht_f": round(tht, 1),
            "gl_injection_rate_mscfd": round(
                self._noise.gaussian(self.injection_rate_mscfd, 5.0, min_val=0), 1
            ),
            "gl_injection_pressure_psi": round(
                self._noise.gaussian(self.injection_pressure_psi, 2.0, min_val=200), 1
            ),
            "choke_size_64ths": self.choke_size_64ths,
            "flow_rate_bpd": round(
                self._noise.with_outliers(effective_flow, 8.0, min_val=0), 1
            ),
            "water_cut_pct": round(base["water_cut_pct"], 2),
            "gor_scf_stb": round(self._noise.gaussian(total_gor, 5.0, min_val=0), 1),
        }

        return telemetry

    def _glpc_factor(self, injection_mscfd: float) -> float:
        """Gas lift performance curve factor.

        Production peaks at optimal injection rate, then declines due
        to backpressure at excessive rates.
        """
        if self.optimal_injection_mscfd <= 0:
            return 1.0
        ratio = injection_mscfd / self.optimal_injection_mscfd
        if ratio <= 1.0:
            return 0.6 + 0.4 * ratio
        else:
            # Past optimal: slight decline
            excess = ratio - 1.0
            return 1.0 - 0.1 * excess ** 2

    def set_casing_heading(
        self,
        active: bool,
        period_min: float = 15.0,
        amplitude_psi: float = 100.0,
    ) -> None:
        """Activate or deactivate casing heading oscillation."""
        self._heading_active = active
        self._heading_period_min = period_min
        self._heading_amplitude_psi = amplitude_psi

    def get_static_attributes(self) -> dict[str, Any]:
        """Gas lift-specific server attributes."""
        attrs = super().get_static_attributes()
        attrs.update({
            # Valve/mandrel configuration
            "gl_num_mandrels": self.num_mandrels,
            "gl_operating_valve_depth_ft": self.operating_valve_depth_ft,
            "gl_valve_port_size_64ths": self.valve_port_size_64ths,
            "gl_valve_type": self.valve_type,
            "gl_valve_depths_ft": self.valve_depths_ft,
            "gl_valve_opening_psi": self.valve_opening_psi,
            "gl_valve_closing_psi": self.valve_closing_psi,
            "gl_annular_volume_bbl": self.annular_volume_bbl,
            # Injection parameters
            "gl_optimal_injection_mscfd": self.optimal_injection_mscfd,
            "gl_max_injection_mscfd": self.max_injection_mscfd,
            "gl_design_injection_mscfd": self.design_injection_mscfd,
            "gl_injection_pressure_psi": self.injection_pressure_psi,
            # Gas infrastructure
            "gl_gas_supply_pressure_psi": self.gas_supply_pressure_psi,
            "gl_gas_max_available_mscfd": self.gas_max_available_mscfd,
            "gl_gas_cost_usd_mscf": self.gas_cost_usd_mscf,
            # Choke
            "gl_choke_size_64ths": self.choke_size_64ths,
            "install_date": "",
        })
        return attrs
