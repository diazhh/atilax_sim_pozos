"""Simulation scenarios for different operating conditions."""

from .normal_operation import NormalOperationScenario
from .pump_degradation import PumpDegradationScenario
from .gas_interference import GasInterferenceScenario
from .water_breakthrough import WaterBreakthroughScenario
from .casing_heading import CasingHeadingScenario
from .electrical_issues import ElectricalIssuesScenario
from .well_loading import WellLoadingScenario

__all__ = [
    "NormalOperationScenario",
    "PumpDegradationScenario",
    "GasInterferenceScenario",
    "WaterBreakthroughScenario",
    "CasingHeadingScenario",
    "ElectricalIssuesScenario",
    "WellLoadingScenario",
]
