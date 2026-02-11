"""ESP (Electric Submersible Pump) well model.

Simulates pump performance curves, motor electrical parameters,
VSD operation, vibration, and insulation resistance with realistic
correlations between variables.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from models.well_model import WellModel, LiftType, WellStatus
from utils.units import UnitConverter


@dataclass
class ESPModel(WellModel):
    """ESP well simulation model.

    Extends WellModel with ESP-specific equipment parameters,
    pump curves, and correlated telemetry generation.
    """

    # Pump parameters
    pump_model: str = "DN1750"
    pump_stages: int = 200
    design_rate_bpd: float = 1200.0
    design_head_ft: float = 5000.0
    bep_rate_bpd: float = 1000.0
    bep_head_ft_per_stage: float = 25.0
    efficiency_at_bep: float = 0.58
    min_flow_bpd: float = 300.0
    pump_efficiency: float = 0.58  # Current efficiency (degrades over time)

    # Motor parameters
    motor_hp: float = 150.0
    motor_voltage_v: float = 2200.0
    motor_amperage_a: float = 45.0
    motor_power_factor: float = 0.85
    motor_poles: int = 2
    motor_temp_max_f: float = 350.0

    # VSD parameters
    vsd_installed: bool = True
    vsd_frequency_hz: float = 60.0
    vsd_nominal_hz: float = 60.0

    # Alarm/shutdown thresholds (well-specific)
    vibration_alarm_ips: float = 0.35
    vibration_shutdown_ips: float = 0.50
    motor_temp_alarm_f: float = 320.0
    insulation_alarm_mohm: float = 200.0
    underload_pct: float = 30.0
    overload_pct: float = 110.0

    # Operating state (evolves during simulation)
    current_intake_pressure_psi: float = 800.0
    current_discharge_pressure_psi: float = 3000.0
    current_motor_temp_f: float = 220.0
    current_vibration_ips: float = 0.08
    current_insulation_mohm: float = 1200.0

    def __post_init__(self) -> None:
        self.lift_type = LiftType.ESP

    def step(self, dt_days: float, sim_time: datetime) -> dict[str, Any]:
        """Generate ESP telemetry for one time step."""
        if self.status != WellStatus.PRODUCING:
            return self._shut_in_telemetry(sim_time)

        base = super().step(dt_days, sim_time)
        if not self.reservoir or not self.fluid:
            return base

        flow_rate = base.get("flow_rate_bpd", 0)
        water_cut = base.get("water_cut_pct", 0) / 100.0

        # Frequency ratio for affinity laws
        freq_ratio = self.vsd_frequency_hz / self.vsd_nominal_hz

        # Pump head from affinity laws: H ∝ (N/N0)²
        head_at_rate = self._pump_head(flow_rate, freq_ratio)

        # Pressures
        gradient = self.fluid.fluid_gradient(water_cut)
        intake_p = self.reservoir.current_pressure_psi - gradient * (
            self.perforations_top_ft - self.pump_depth_ft
        )
        intake_p = max(intake_p, 50)
        discharge_p = intake_p + head_at_rate * gradient

        # Motor loading
        hydraulic_hp = UnitConverter.pump_hydraulic_hp(flow_rate, head_at_rate * gradient)
        brake_hp = hydraulic_hp / max(self.pump_efficiency, 0.1)
        load_factor = brake_hp / max(self.motor_hp, 1)

        # Electrical: current proportional to load
        # Floor at 20% no-load current (motor always draws magnetising current)
        current = max(self.motor_amperage_a * load_factor * freq_ratio,
                      self.motor_amperage_a * 0.2 * freq_ratio)
        voltage = self.motor_voltage_v * freq_ratio
        power_kw = UnitConverter.three_phase_power_kw(voltage, current, self.motor_power_factor)

        # Motor temperature: function of load and ambient
        hour = sim_time.hour + sim_time.minute / 60.0
        diurnal = self._noise.diurnal_factor(hour, amplitude=0.01)
        base_temp = self.reservoir.temperature_f + 30 * load_factor
        motor_temp = base_temp * diurnal

        # Vibration: increases with flow deviation from BEP
        flow_deviation = abs(flow_rate - self.bep_rate_bpd) / max(self.bep_rate_bpd, 1)
        base_vibration = 0.05 + 0.3 * flow_deviation ** 2
        vibration_x = self._noise.with_outliers(base_vibration, noise_pct=15.0, min_val=0.01)
        vibration_y = self._noise.with_outliers(base_vibration, noise_pct=15.0, min_val=0.01)

        # Insulation: slow random walk
        self.current_insulation_mohm = self._noise.random_walk(
            self.current_insulation_mohm, step_size=2.0, min_val=50, max_val=2000
        )

        # Wellhead pressure
        thp = discharge_p - gradient * self.pump_depth_ft
        thp = max(thp, 20)

        # Casing head pressure
        chp = intake_p + gradient * (self.pump_depth_ft - self.perforations_top_ft) * 0.5
        chp = max(chp, 30)

        # Apply anomaly modifiers
        efficiency_mod = self.anomaly_modifiers.get("efficiency", 1.0)
        current_mod = self.anomaly_modifiers.get("current", 1.0)
        vibration_mod = self.anomaly_modifiers.get("vibration", 1.0)
        temp_mod = self.anomaly_modifiers.get("temperature", 1.0)

        # Calculate pump efficiency (floor at 5% — a running pump always has some efficiency)
        hydraulic_power = (discharge_p - intake_p) * flow_rate / 1714  # HP
        pump_efficiency_pct = min(100, max(5, (hydraulic_power / max(power_kw * 1.341, 0.1)) * 100))

        telemetry: dict[str, Any] = {
            "thp_psi": round(self._noise.gaussian(thp, 2.0, min_val=10), 1),
            "chp_psi": round(self._noise.gaussian(chp, 2.0, min_val=10), 1),
            "tht_f": round(self._noise.gaussian(
                self.reservoir.temperature_f * 0.6 * diurnal, 0.5, min_val=80
            ), 1),
            "intake_pressure_psi": round(self._noise.gaussian(intake_p, 2.0, min_val=50), 1),
            "discharge_pressure_psi": round(self._noise.gaussian(discharge_p, 2.0, min_val=100), 1),
            "motor_temp_f": round(self._noise.gaussian(motor_temp * temp_mod, 0.5, min_val=100), 1),
            "intake_temp_f": round(self._noise.gaussian(
                self.reservoir.temperature_f * 0.85, 0.5, min_val=100
            ), 1),
            "motor_current_a": round(self._noise.gaussian(
                current * current_mod, 3.0, min_val=5
            ), 2),
            "motor_voltage_v": round(self._noise.gaussian(voltage, 1.5, min_val=400), 1),
            "motor_power_kw": round(self._noise.gaussian(power_kw, 2.0, min_val=0), 2),
            "vsd_frequency_hz": round(self._noise.gaussian(
                self.vsd_frequency_hz, 0.3
            ), 2),
            "vibration_x_ips": round(vibration_x * vibration_mod, 4),
            "vibration_y_ips": round(vibration_y * vibration_mod, 4),
            "insulation_mohm": round(self.current_insulation_mohm, 0),
            "flow_rate_bpd": round(base["flow_rate_bpd"] * efficiency_mod, 1),
            "water_cut_pct": round(base["water_cut_pct"], 2),
            "gor_scf_stb": round(base["gor_scf_stb"], 1),
            "pump_efficiency_pct": round(self._noise.gaussian(pump_efficiency_pct, 1.5, min_val=0, max_val=100), 1),
        }

        # Add aliases for ThingsBoard rule compatibility
        telemetry["frequency_hz"] = telemetry["vsd_frequency_hz"]
        telemetry["motor_temperature_f"] = telemetry["motor_temp_f"]
        telemetry["vibration_ips"] = round(max(vibration_x, vibration_y) * vibration_mod, 4)
        telemetry["tubing_pressure_psi"] = telemetry["thp_psi"]
        telemetry["casing_pressure_psi"] = telemetry["chp_psi"]
        telemetry["wellhead_temperature_f"] = telemetry["tht_f"]

        return telemetry

    def _pump_head(self, flow_rate: float, freq_ratio: float) -> float:
        """Simplified pump head curve using parabolic approximation.

        H = H_shutoff * [1 - (Q/Q_max)²] * (N/N0)²
        """
        h_shutoff = self.design_head_ft * 1.3
        q_max = self.design_rate_bpd * 1.4 * freq_ratio

        if q_max <= 0:
            return 0.0

        q_ratio = min(flow_rate / q_max, 1.0)
        head = h_shutoff * (1 - q_ratio ** 2) * freq_ratio ** 2
        return max(head, 0)

    def get_static_attributes(self) -> dict[str, Any]:
        """ESP-specific attributes added to base well attributes."""
        attrs = super().get_static_attributes()
        attrs.update({
            # Pump
            "esp_pump_model": self.pump_model,
            "esp_pump_stages": self.pump_stages,
            "esp_design_rate_bpd": self.design_rate_bpd,
            "esp_design_head_ft": self.design_head_ft,
            "esp_bep_rate_bpd": self.bep_rate_bpd,
            "esp_bep_head_ft_per_stage": self.bep_head_ft_per_stage,
            "esp_efficiency_at_bep": self.efficiency_at_bep,
            "esp_min_flow_bpd": self.min_flow_bpd,
            # Motor
            "esp_motor_hp": self.motor_hp,
            "esp_motor_voltage_v": self.motor_voltage_v,
            "esp_motor_amperage_a": self.motor_amperage_a,
            "esp_motor_power_factor": self.motor_power_factor,
            "esp_motor_temp_max_f": self.motor_temp_max_f,
            # VSD
            "esp_vsd_installed": self.vsd_installed,
            "esp_vsd_nominal_hz": self.vsd_nominal_hz,
            # Alarm thresholds (well-specific)
            "esp_vibration_alarm_ips": self.vibration_alarm_ips,
            "esp_vibration_shutdown_ips": self.vibration_shutdown_ips,
            "esp_motor_temp_alarm_f": self.motor_temp_alarm_f,
            "esp_insulation_alarm_mohm": self.insulation_alarm_mohm,
            "esp_underload_pct": self.underload_pct,
            "esp_overload_pct": self.overload_pct,
            "install_date": "",
        })
        return attrs
