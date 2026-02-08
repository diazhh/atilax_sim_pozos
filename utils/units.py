"""Unit conversion utilities for oilfield calculations."""

from __future__ import annotations

import math


class UnitConverter:
    """Oilfield unit conversions."""

    # ── Pressure ─────────────────────────────────────────────────────────

    @staticmethod
    def psi_to_kpa(psi: float) -> float:
        return psi * 6.894757

    @staticmethod
    def kpa_to_psi(kpa: float) -> float:
        return kpa / 6.894757

    @staticmethod
    def psi_to_bar(psi: float) -> float:
        return psi * 0.0689476

    @staticmethod
    def bar_to_psi(bar: float) -> float:
        return bar / 0.0689476

    # ── Temperature ──────────────────────────────────────────────────────

    @staticmethod
    def f_to_c(f: float) -> float:
        return (f - 32) * 5.0 / 9.0

    @staticmethod
    def c_to_f(c: float) -> float:
        return c * 9.0 / 5.0 + 32

    @staticmethod
    def f_to_r(f: float) -> float:
        return f + 459.67

    @staticmethod
    def c_to_k(c: float) -> float:
        return c + 273.15

    # ── Length ────────────────────────────────────────────────────────────

    @staticmethod
    def ft_to_m(ft: float) -> float:
        return ft * 0.3048

    @staticmethod
    def m_to_ft(m: float) -> float:
        return m / 0.3048

    @staticmethod
    def in_to_cm(inches: float) -> float:
        return inches * 2.54

    # ── Flow rate ────────────────────────────────────────────────────────

    @staticmethod
    def bpd_to_m3d(bpd: float) -> float:
        return bpd * 0.158987

    @staticmethod
    def m3d_to_bpd(m3d: float) -> float:
        return m3d / 0.158987

    @staticmethod
    def mscfd_to_m3d(mscfd: float) -> float:
        """Thousand standard cubic feet/day to m3/day."""
        return mscfd * 28.3168

    # ── Volume ───────────────────────────────────────────────────────────

    @staticmethod
    def bbl_to_m3(bbl: float) -> float:
        return bbl * 0.158987

    @staticmethod
    def bbl_to_gal(bbl: float) -> float:
        return bbl * 42.0

    # ── Mass / Density ───────────────────────────────────────────────────

    @staticmethod
    def api_to_sg(api: float) -> float:
        return 141.5 / (api + 131.5)

    @staticmethod
    def sg_to_api(sg: float) -> float:
        return 141.5 / sg - 131.5

    @staticmethod
    def ppg_to_sg(ppg: float) -> float:
        return ppg / 8.33

    # ── Power / Energy ───────────────────────────────────────────────────

    @staticmethod
    def hp_to_kw(hp: float) -> float:
        return hp * 0.7457

    @staticmethod
    def kw_to_hp(kw: float) -> float:
        return kw / 0.7457

    # ── Torque ───────────────────────────────────────────────────────────

    @staticmethod
    def ftlb_to_nm(ftlb: float) -> float:
        return ftlb * 1.35582

    @staticmethod
    def nm_to_ftlb(nm: float) -> float:
        return nm / 1.35582

    # ── Derived calculations ─────────────────────────────────────────────

    @staticmethod
    def hydrostatic_pressure_psi(
        depth_ft: float,
        fluid_gradient_psi_ft: float,
    ) -> float:
        """Hydrostatic pressure from depth and fluid gradient."""
        return depth_ft * fluid_gradient_psi_ft

    @staticmethod
    def pump_hydraulic_hp(
        rate_bpd: float,
        differential_psi: float,
    ) -> float:
        """Hydraulic horsepower of a pump."""
        return rate_bpd * differential_psi / 136048.0

    @staticmethod
    def specific_energy_kwh_bbl(
        power_kw: float,
        rate_bpd: float,
    ) -> float:
        """Specific energy consumption (kWh/bbl)."""
        if rate_bpd <= 0:
            return 0.0
        return power_kw * 24.0 / rate_bpd

    @staticmethod
    def three_phase_power_kw(
        voltage_v: float,
        current_a: float,
        power_factor: float = 0.85,
    ) -> float:
        """Three-phase electrical power (kW)."""
        return voltage_v * current_a * math.sqrt(3) * power_factor / 1000.0
