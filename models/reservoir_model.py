"""Simplified reservoir model with IPR and pressure depletion.

Models inflow performance (Vogel IPR), reservoir pressure decline
via simplified material balance, and water cut evolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.random import Generator

from utils.correlations import PVTCorrelations


@dataclass
class ReservoirModel:
    """Simplified reservoir model for a single well drainage area.

    Attributes:
        initial_pressure_psi: Original reservoir pressure.
        current_pressure_psi: Current average reservoir pressure.
        temperature_f: Reservoir temperature (F).
        bubble_point_psi: Bubble-point pressure (psi).
        api_gravity: Oil API gravity.
        gor_scf_stb: Initial solution GOR.
        water_cut: Current water fraction (0-1).
        water_cut_initial: Initial water cut.
        productivity_index: J (bpd/psi) or None to use Vogel.
        ipr_qmax_bpd: Absolute open-flow potential for Vogel.
        ipr_model: "vogel" | "darcy".
        drive_mechanism: "solution_gas" | "water_drive" | "gas_cap".
        cumulative_oil_stb: Cumulative oil produced (STB).
        ooip_stb: Estimated OOIP for pressure depletion.
    """

    initial_pressure_psi: float
    current_pressure_psi: float
    temperature_f: float
    bubble_point_psi: float
    api_gravity: float
    gor_scf_stb: float
    water_cut: float
    water_cut_initial: float
    productivity_index: float | None = None
    ipr_qmax_bpd: float = 0.0
    ipr_model: str = "vogel"
    drive_mechanism: str = "solution_gas"
    cumulative_oil_stb: float = 0.0
    ooip_stb: float = 500_000.0

    # Fetkovich IPR parameters (for multi-rate test wells)
    fetkovich_c: float = 0.0
    fetkovich_n: float = 0.85

    # Gas and water gravity
    gas_gravity: float = 0.75
    water_gravity: float = 1.05

    _rng: Generator = field(default_factory=lambda: np.random.default_rng())

    def set_rng(self, rng: Generator) -> None:
        self._rng = rng

    def flow_rate_bpd(self, pwf_psi: float) -> float:
        """Calculate inflow rate (bpd liquid) at given flowing BHP.

        Args:
            pwf_psi: Bottom-hole flowing pressure (psi).

        Returns:
            Liquid production rate (bpd).
        """
        pr = self.current_pressure_psi
        if pwf_psi >= pr or pr <= 0:
            return 0.0

        if self.ipr_model == "vogel" and pr <= self.bubble_point_psi:
            q_liquid = PVTCorrelations.vogel_ipr(pr, self.ipr_qmax_bpd, pwf_psi)
        else:
            j = self.productivity_index or self._estimate_pi()
            q_liquid = j * (pr - pwf_psi)

        return max(q_liquid, 0.0)

    def oil_rate_bpd(self, pwf_psi: float) -> float:
        """Net oil rate accounting for water cut."""
        return self.flow_rate_bpd(pwf_psi) * (1 - self.water_cut)

    def water_rate_bpd(self, pwf_psi: float) -> float:
        """Water rate from water cut."""
        return self.flow_rate_bpd(pwf_psi) * self.water_cut

    def update_pressure(self, oil_produced_stb: float, dt_days: float) -> None:
        """Simplified material-balance pressure update.

        Pressure declines proportional to cumulative recovery factor.
        Water-drive reservoirs decline more slowly.
        """
        self.cumulative_oil_stb += oil_produced_stb

        recovery_factor = self.cumulative_oil_stb / self.ooip_stb if self.ooip_stb > 0 else 0

        if self.drive_mechanism == "water_drive":
            # Pressure support from aquifer — slower decline
            pressure_factor = 1.0 - 0.3 * recovery_factor
        elif self.drive_mechanism == "gas_cap":
            pressure_factor = 1.0 - 0.5 * recovery_factor
        else:
            # Solution gas — steeper decline
            pressure_factor = 1.0 - 0.7 * recovery_factor

        self.current_pressure_psi = max(
            self.initial_pressure_psi * pressure_factor,
            100.0,  # Minimum reservoir pressure
        )

    def update_water_cut(self, dt_days: float) -> None:
        """Gradual water cut increase depending on drive mechanism.

        Water-drive fields have faster BSW increase.
        """
        if self.drive_mechanism == "water_drive":
            daily_increase = 0.0003  # ~11% per year
        elif self.drive_mechanism == "gas_cap":
            daily_increase = 0.0002
        else:
            daily_increase = 0.00015

        # Add small randomness
        daily_increase *= (1 + self._rng.normal(0, 0.1))
        self.water_cut = min(self.water_cut + daily_increase * dt_days, 0.98)

    def step(self, pwf_psi: float, dt_days: float) -> dict[str, float]:
        """Advance reservoir state by dt_days.

        Args:
            pwf_psi: Bottom-hole flowing pressure.
            dt_days: Time step in days.

        Returns:
            Dict with flow rates and updated state.
        """
        q_liquid = self.flow_rate_bpd(pwf_psi)
        q_oil = q_liquid * (1 - self.water_cut)
        q_water = q_liquid * self.water_cut

        oil_produced = q_oil * dt_days
        self.update_pressure(oil_produced, dt_days)
        self.update_water_cut(dt_days)

        return {
            "flow_rate_bpd": q_liquid,
            "oil_rate_bpd": q_oil,
            "water_rate_bpd": q_water,
            "water_cut_pct": self.water_cut * 100,
            "reservoir_pressure_psi": self.current_pressure_psi,
            "gor_scf_stb": self._current_gor(),
        }

    def _estimate_pi(self) -> float:
        """Estimate productivity index from qmax if not provided."""
        if self.ipr_qmax_bpd > 0 and self.current_pressure_psi > 0:
            return self.ipr_qmax_bpd / self.current_pressure_psi
        return 1.0

    def _current_gor(self) -> float:
        """Estimate current GOR based on pressure depletion."""
        if self.current_pressure_psi >= self.bubble_point_psi:
            return self.gor_scf_stb

        # Below bubble point, GOR increases as free gas liberates
        pressure_ratio = self.current_pressure_psi / self.bubble_point_psi
        gor_multiplier = 1.0 + 1.5 * (1.0 - pressure_ratio)
        return self.gor_scf_stb * gor_multiplier

    def get_attributes(self) -> dict[str, object]:
        """Return server attributes for ThingsBoard."""
        attrs: dict[str, object] = {
            "reservoir_pressure_psi": self.initial_pressure_psi,
            "reservoir_temperature_f": self.temperature_f,
            "bubble_point_psi": self.bubble_point_psi,
            "api_gravity": self.api_gravity,
            "gor_scf_stb": self.gor_scf_stb,
            "water_cut_initial_pct": round(self.water_cut_initial * 100, 1),
            "oil_viscosity_cp": PVTCorrelations.beggs_robinson_dead_oil(
                self.temperature_f, self.api_gravity
            ),
            "bo_factor": PVTCorrelations.standing_bo(
                self.temperature_f, self.api_gravity, self.gor_scf_stb
            ),
            "productivity_index_bpd_psi": self.productivity_index or self._estimate_pi(),
            "ipr_model": self.ipr_model,
            "ipr_qmax_bpd": self.ipr_qmax_bpd,
            "drive_mechanism": self.drive_mechanism,
            "gas_gravity": self.gas_gravity,
            "water_gravity": self.water_gravity,
            "ooip_stb": self.ooip_stb,
        }
        # Add Fetkovich parameters only if applicable
        if self.fetkovich_c > 0:
            attrs["fetkovich_c"] = self.fetkovich_c
            attrs["fetkovich_n"] = self.fetkovich_n
        return attrs
