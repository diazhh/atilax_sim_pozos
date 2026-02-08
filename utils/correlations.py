"""PVT correlations for petroleum fluid properties.

Implements Standing, Vasquez-Beggs, and other standard oilfield correlations
for bubble point, solution GOR, formation volume factor, and viscosity.
"""

from __future__ import annotations

import math


class PVTCorrelations:
    """Standard petroleum PVT correlations."""

    # ── Bubble point pressure ────────────────────────────────────────────

    @staticmethod
    def standing_pb(
        temperature_f: float,
        api_gravity: float,
        gor_scf_stb: float,
        gas_sg: float = 0.75,
    ) -> float:
        """Standing correlation for bubble-point pressure (psi).

        Args:
            temperature_f: Reservoir temperature (F).
            api_gravity: Oil API gravity.
            gor_scf_stb: Solution gas-oil ratio (scf/STB).
            gas_sg: Gas specific gravity.
        """
        if gor_scf_stb <= 0:
            return 0.0
        a = 0.00091 * temperature_f - 0.0125 * api_gravity
        yg = gas_sg
        pb = 18.2 * ((gor_scf_stb / yg) ** 0.83 * 10 ** a - 1.4)
        return max(pb, 14.7)

    # ── Solution GOR ─────────────────────────────────────────────────────

    @staticmethod
    def standing_rs(
        pressure_psi: float,
        temperature_f: float,
        api_gravity: float,
        gas_sg: float = 0.75,
    ) -> float:
        """Standing correlation for solution GOR (scf/STB).

        Valid below bubble point.
        """
        if pressure_psi <= 14.7:
            return 0.0
        a = 0.00091 * temperature_f - 0.0125 * api_gravity
        rs = gas_sg * ((pressure_psi / 18.2 + 1.4) * 10 ** (-a)) ** 1.2048
        return max(rs, 0.0)

    # ── Formation volume factor ──────────────────────────────────────────

    @staticmethod
    def standing_bo(
        temperature_f: float,
        api_gravity: float,
        gor_scf_stb: float,
        gas_sg: float = 0.75,
    ) -> float:
        """Standing correlation for Bo (bbl/STB) at bubble point."""
        oil_sg = 141.5 / (api_gravity + 131.5)
        f = gor_scf_stb * (gas_sg / oil_sg) ** 0.5 + 1.25 * temperature_f
        bo = 0.9759 + 0.00012 * f ** 1.2
        return max(bo, 1.0)

    # ── Oil viscosity ────────────────────────────────────────────────────

    @staticmethod
    def beggs_robinson_dead_oil(
        temperature_f: float,
        api_gravity: float,
    ) -> float:
        """Beggs-Robinson dead-oil viscosity (cp).

        Args:
            temperature_f: Temperature (F).
            api_gravity: API gravity.
        """
        z = 3.0324 - 0.02023 * api_gravity
        y = 10.0 ** z
        x = y * temperature_f ** (-1.163)
        mu_od = 10.0 ** x - 1.0
        return max(mu_od, 0.1)

    @staticmethod
    def beggs_robinson_live_oil(
        mu_dead_cp: float,
        rs_scf_stb: float,
    ) -> float:
        """Beggs-Robinson live-oil viscosity (cp).

        Args:
            mu_dead_cp: Dead-oil viscosity (cp).
            rs_scf_stb: Solution GOR (scf/STB).
        """
        if rs_scf_stb <= 0:
            return mu_dead_cp
        a = 10.715 * (rs_scf_stb + 100) ** (-0.515)
        b = 5.44 * (rs_scf_stb + 150) ** (-0.338)
        mu_live = a * mu_dead_cp ** b
        return max(mu_live, 0.1)

    # ── Gas Z-factor (Hall-Yarborough) simplified ────────────────────────

    @staticmethod
    def gas_z_factor(
        pressure_psi: float,
        temperature_f: float,
        gas_sg: float = 0.75,
    ) -> float:
        """Simplified gas compressibility factor (Brill-Beggs).

        Uses pseudo-critical correlations for natural gas.
        """
        tpc = 168 + 325 * gas_sg - 12.5 * gas_sg ** 2
        ppc = 677 + 15.0 * gas_sg - 37.5 * gas_sg ** 2
        tpr = (temperature_f + 460) / tpc
        ppr = pressure_psi / ppc

        a = 1.39 * (tpr - 0.92) ** 0.5 - 0.36 * tpr - 0.101
        b = (0.62 - 0.23 * tpr) * ppr
        c = (0.066 / (tpr - 0.86) - 0.037) * ppr ** 2
        d = (0.32 / (10 ** (9 * (tpr - 1)))) * ppr ** 6
        e = b + c + d

        z = a + (1 - a) * math.exp(-e) + 0.132  # simplified adjustment
        return max(min(z, 1.5), 0.3)

    # ── Water density ────────────────────────────────────────────────────

    @staticmethod
    def water_density_ppg(
        temperature_f: float,
        salinity_ppm: float = 30000,
    ) -> float:
        """Water density (ppg) with temperature and salinity corrections."""
        rho_w = 8.34 * (1 + 3.6e-6 * salinity_ppm) * (
            1 - 3.6e-4 * (temperature_f - 60)
        )
        return max(rho_w, 8.0)

    # ── Composite fluid properties ───────────────────────────────────────

    @staticmethod
    def fluid_gradient_psi_ft(
        api_gravity: float,
        water_cut: float,
        water_sg: float = 1.05,
    ) -> float:
        """Mixed fluid gradient (psi/ft).

        Args:
            api_gravity: Oil API gravity.
            water_cut: Water cut fraction (0-1).
            water_sg: Water specific gravity.
        """
        oil_sg = 141.5 / (api_gravity + 131.5)
        mixed_sg = water_cut * water_sg + (1 - water_cut) * oil_sg
        return mixed_sg * 0.433

    # ── IPR helpers ──────────────────────────────────────────────────────

    @staticmethod
    def vogel_ipr(
        pr_psi: float,
        qmax_bpd: float,
        pwf_psi: float,
    ) -> float:
        """Vogel IPR for flow rate below bubble point.

        q = qmax * [1 - 0.2*(Pwf/Pr) - 0.8*(Pwf/Pr)^2]
        """
        if pr_psi <= 0 or pwf_psi >= pr_psi:
            return 0.0
        ratio = pwf_psi / pr_psi
        q = qmax_bpd * (1 - 0.2 * ratio - 0.8 * ratio ** 2)
        return max(q, 0.0)

    @staticmethod
    def productivity_index(
        pr_psi: float,
        qtest_bpd: float,
        pwf_test_psi: float,
    ) -> float:
        """Calculate productivity index J (bpd/psi) from test data."""
        dp = pr_psi - pwf_test_psi
        if dp <= 0:
            return 0.0
        return qtest_bpd / dp
