"""Simplified PVT fluid model.

Wraps PVT correlations into a stateful fluid object for a specific
wellbore section, computing properties at given P and T conditions.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.correlations import PVTCorrelations


@dataclass
class FluidModel:
    """PVT fluid model for a specific well.

    Attributes:
        api_gravity: Oil API gravity.
        gas_sg: Gas specific gravity.
        water_sg: Water specific gravity.
        reservoir_temperature_f: Reservoir temperature (F).
        gor_scf_stb: Original solution GOR at bubble point.
        bubble_point_psi: Bubble point pressure.
        salinity_ppm: Formation water salinity.
    """

    api_gravity: float
    gas_sg: float = 0.75
    water_sg: float = 1.05
    reservoir_temperature_f: float = 180.0
    gor_scf_stb: float = 200.0
    bubble_point_psi: float = 1500.0
    salinity_ppm: float = 30000.0

    @property
    def oil_sg(self) -> float:
        return 141.5 / (self.api_gravity + 131.5)

    def solution_gor(self, pressure_psi: float, temperature_f: float | None = None) -> float:
        """Solution GOR at given pressure (scf/STB)."""
        t = temperature_f or self.reservoir_temperature_f
        if pressure_psi >= self.bubble_point_psi:
            return self.gor_scf_stb
        return PVTCorrelations.standing_rs(pressure_psi, t, self.api_gravity, self.gas_sg)

    def bo(self, pressure_psi: float, temperature_f: float | None = None) -> float:
        """Oil formation volume factor (bbl/STB)."""
        t = temperature_f or self.reservoir_temperature_f
        rs = self.solution_gor(pressure_psi, t)
        return PVTCorrelations.standing_bo(t, self.api_gravity, rs, self.gas_sg)

    def dead_oil_viscosity(self, temperature_f: float | None = None) -> float:
        """Dead-oil viscosity (cp)."""
        t = temperature_f or self.reservoir_temperature_f
        return PVTCorrelations.beggs_robinson_dead_oil(t, self.api_gravity)

    def live_oil_viscosity(
        self,
        pressure_psi: float,
        temperature_f: float | None = None,
    ) -> float:
        """Live-oil viscosity accounting for dissolved gas (cp)."""
        t = temperature_f or self.reservoir_temperature_f
        mu_dead = self.dead_oil_viscosity(t)
        rs = self.solution_gor(pressure_psi, t)
        return PVTCorrelations.beggs_robinson_live_oil(mu_dead, rs)

    def gas_z_factor(self, pressure_psi: float, temperature_f: float | None = None) -> float:
        """Gas compressibility factor."""
        t = temperature_f or self.reservoir_temperature_f
        return PVTCorrelations.gas_z_factor(pressure_psi, t, self.gas_sg)

    def fluid_gradient(self, water_cut: float) -> float:
        """Mixed fluid gradient (psi/ft).

        Args:
            water_cut: Water cut fraction (0-1).
        """
        return PVTCorrelations.fluid_gradient_psi_ft(
            self.api_gravity, water_cut, self.water_sg
        )

    def water_density_ppg(self, temperature_f: float | None = None) -> float:
        """Formation water density (ppg)."""
        t = temperature_f or self.reservoir_temperature_f
        return PVTCorrelations.water_density_ppg(t, self.salinity_ppm)
