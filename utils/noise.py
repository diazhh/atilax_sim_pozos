"""Noise generator for realistic telemetry simulation.

Provides Gaussian noise, outliers, diurnal cycles, and correlated
multi-variable noise to produce realistic oilfield sensor data.
"""

from __future__ import annotations

import numpy as np
from numpy.random import Generator


class NoiseGenerator:
    """Generate realistic sensor noise for well telemetry."""

    def __init__(self, rng: Generator | None = None) -> None:
        self.rng = rng or np.random.default_rng()

    def gaussian(
        self,
        value: float,
        noise_pct: float = 2.0,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> float:
        """Add Gaussian noise as a percentage of the value.

        Args:
            value: Base value to add noise to.
            noise_pct: Standard deviation as percentage of value.
            min_val: Optional lower clamp.
            max_val: Optional upper clamp.
        """
        if value == 0:
            return 0.0
        sigma = abs(value) * noise_pct / 100.0
        noisy = value + self.rng.normal(0, sigma)
        if min_val is not None:
            noisy = max(noisy, min_val)
        if max_val is not None:
            noisy = min(noisy, max_val)
        return float(noisy)

    def with_outliers(
        self,
        value: float,
        noise_pct: float = 2.0,
        outlier_prob: float = 0.005,
        outlier_sigma: float = 3.0,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> float:
        """Add Gaussian noise with occasional outliers.

        Args:
            value: Base value.
            noise_pct: Normal noise standard deviation (% of value).
            outlier_prob: Probability of an outlier sample.
            outlier_sigma: Outlier deviation in multiples of sigma.
            min_val: Lower clamp.
            max_val: Upper clamp.
        """
        if self.rng.random() < outlier_prob:
            sigma = abs(value) * noise_pct / 100.0
            deviation = sigma * outlier_sigma * self.rng.choice([-1, 1])
            noisy = value + deviation
        else:
            noisy = self.gaussian(value, noise_pct)
        if min_val is not None:
            noisy = max(noisy, min_val)
        if max_val is not None:
            noisy = min(noisy, max_val)
        return float(noisy)

    def diurnal_factor(self, hour_of_day: float, amplitude: float = 0.02) -> float:
        """Sinusoidal diurnal cycle factor peaking at ~2PM.

        Args:
            hour_of_day: 0-24 fractional hour.
            amplitude: Peak-to-peak amplitude as fraction (0.02 = ±2%).

        Returns:
            Multiplicative factor (e.g., 0.98 to 1.02).
        """
        phase = 2 * np.pi * (hour_of_day - 14) / 24.0
        return 1.0 + amplitude * np.sin(phase)

    def correlated_pair(
        self,
        value_a: float,
        value_b: float,
        noise_pct_a: float,
        noise_pct_b: float,
        correlation: float = 0.7,
    ) -> tuple[float, float]:
        """Generate two correlated noisy values.

        Args:
            value_a: Base value A.
            value_b: Base value B.
            noise_pct_a: Noise % for A.
            noise_pct_b: Noise % for B.
            correlation: Pearson correlation (-1 to 1).

        Returns:
            Tuple of (noisy_a, noisy_b).
        """
        mean = [0, 0]
        cov = [[1, correlation], [correlation, 1]]
        z = self.rng.multivariate_normal(mean, cov)

        sigma_a = abs(value_a) * noise_pct_a / 100.0
        sigma_b = abs(value_b) * noise_pct_b / 100.0

        noisy_a = value_a + z[0] * sigma_a
        noisy_b = value_b + z[1] * sigma_b
        return float(noisy_a), float(noisy_b)

    def stuck_sensor(self, value: float, stuck_value: float | None = None) -> float:
        """Return a stuck sensor value (same value repeated).

        Args:
            value: Current true value (ignored if stuck_value provided).
            stuck_value: The value the sensor is stuck at.
        """
        return stuck_value if stuck_value is not None else value

    def sensor_drift(
        self,
        value: float,
        drift_rate: float,
        elapsed_hours: float,
    ) -> float:
        """Apply linear sensor drift over time.

        Args:
            value: True value.
            drift_rate: Drift per hour (absolute units).
            elapsed_hours: Hours since drift started.
        """
        return value + drift_rate * elapsed_hours

    def random_walk(
        self,
        current: float,
        step_size: float = 0.5,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> float:
        """One step of a random walk.

        Args:
            current: Current value.
            step_size: Standard deviation of step.
            min_val: Lower bound.
            max_val: Upper bound.
        """
        new_val = current + self.rng.normal(0, step_size)
        if min_val is not None:
            new_val = max(new_val, min_val)
        if max_val is not None:
            new_val = min(new_val, max_val)
        return float(new_val)
