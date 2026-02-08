"""Production decline generator using Arps decline curves.

Applies exponential, hyperbolic, or harmonic decline to
well production over time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.random import Generator


@dataclass
class DeclineParameters:
    """Arps decline curve parameters.

    Attributes:
        qi_bpd: Initial production rate (bpd).
        di: Initial decline rate (1/year).
        b: Arps exponent (0 = exponential, 0-1 = hyperbolic, 1 = harmonic).
        min_rate_bpd: Economic limit rate.
    """

    qi_bpd: float
    di: float
    b: float = 0.5
    min_rate_bpd: float = 5.0


class DeclineGenerator:
    """Generate production decline factors over time.

    Supports Arps exponential, hyperbolic, and harmonic decline.
    """

    def __init__(self, rng: Generator | None = None) -> None:
        self.rng = rng or np.random.default_rng()

    def exponential_rate(self, params: DeclineParameters, t_days: float) -> float:
        """Exponential decline: q(t) = qi * exp(-Di * t).

        Args:
            params: Decline parameters.
            t_days: Time in days since start.
        """
        t_years = t_days / 365.0
        rate = params.qi_bpd * math.exp(-params.di * t_years)
        return max(rate, params.min_rate_bpd)

    def hyperbolic_rate(self, params: DeclineParameters, t_days: float) -> float:
        """Hyperbolic decline: q(t) = qi / (1 + b*Di*t)^(1/b).

        Args:
            params: Decline parameters.
            t_days: Time in days since start.
        """
        if params.b <= 0:
            return self.exponential_rate(params, t_days)
        if params.b >= 1:
            return self.harmonic_rate(params, t_days)

        t_years = t_days / 365.0
        denominator = (1 + params.b * params.di * t_years) ** (1.0 / params.b)
        if denominator <= 0:
            return params.min_rate_bpd
        rate = params.qi_bpd / denominator
        return max(rate, params.min_rate_bpd)

    def harmonic_rate(self, params: DeclineParameters, t_days: float) -> float:
        """Harmonic decline: q(t) = qi / (1 + Di*t).

        Args:
            params: Decline parameters.
            t_days: Time in days since start.
        """
        t_years = t_days / 365.0
        rate = params.qi_bpd / (1 + params.di * t_years)
        return max(rate, params.min_rate_bpd)

    def decline_factor(self, params: DeclineParameters, t_days: float) -> float:
        """Get the multiplicative decline factor at time t.

        Returns q(t) / qi, a value between 0 and 1.
        """
        rate = self.hyperbolic_rate(params, t_days)
        return rate / params.qi_bpd if params.qi_bpd > 0 else 1.0

    def cumulative_production(self, params: DeclineParameters, t_days: float) -> float:
        """Cumulative production over t_days (STB).

        Uses analytical Arps formula for hyperbolic cumulative:
        Np = qi^b / ((1-b)*Di) * [qi^(1-b) - q(t)^(1-b)]  for b != 1
        Np = qi / Di * ln(qi / q(t))                         for b == 1
        """
        t_years = t_days / 365.0
        qt = self.hyperbolic_rate(params, t_days)

        if params.b == 0:
            # Exponential
            if params.di <= 0:
                return params.qi_bpd * t_years * 365
            np_stb = (params.qi_bpd - qt) / params.di * 365
        elif abs(params.b - 1.0) < 1e-6:
            # Harmonic
            if qt <= 0 or params.di <= 0:
                return 0.0
            np_stb = params.qi_bpd / params.di * math.log(params.qi_bpd / qt) * 365
        else:
            # Hyperbolic
            if params.di <= 0:
                return params.qi_bpd * t_years * 365
            factor = params.qi_bpd ** params.b / ((1 - params.b) * params.di)
            np_stb = factor * (
                params.qi_bpd ** (1 - params.b) - qt ** (1 - params.b)
            ) * 365

        return max(np_stb, 0.0)

    def generate_decline_params(
        self,
        initial_rate_bpd: float,
        annual_decline_rate: float,
    ) -> DeclineParameters:
        """Create decline parameters with some randomness.

        Args:
            initial_rate_bpd: Starting production rate.
            annual_decline_rate: Annual nominal decline (0-1).
        """
        # Add ±10% randomness to decline rate
        di = annual_decline_rate * self.rng.uniform(0.9, 1.1)
        # b factor: 0.3-0.7 for most oil wells
        b = self.rng.uniform(0.3, 0.7)
        return DeclineParameters(
            qi_bpd=initial_rate_bpd,
            di=di,
            b=b,
            min_rate_bpd=max(5.0, initial_rate_bpd * 0.02),
        )
