"""Macolla (well pad / station) model.

Groups wells together with shared facilities and an IoT gateway.
Handles well creation based on lift distribution and provides
aggregate production data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
from numpy.random import Generator

from models.well_model import WellModel, LiftType
from models.esp_model import ESPModel
from models.srp_model import SRPModel
from models.gaslift_model import GasLiftModel
from models.pcp_model import PCPModel
from models.reservoir_model import ReservoirModel
from models.fluid_model import FluidModel


@dataclass
class Facility:
    """Surface facility (separator, compressor, tank, heater_treater)."""

    name: str
    facility_type: str
    macolla_name: str
    specs: dict[str, Any] = field(default_factory=dict)

    def get_attributes(self) -> dict[str, Any]:
        attrs = {
            "facility_name": self.name,
            "facility_type": self.facility_type,
            "macolla": self.macolla_name,
        }
        attrs.update(self.specs)
        return attrs


@dataclass
class MacollaModel:
    """Macolla (well pad) containing multiple wells and facilities.

    Attributes:
        name: Macolla identifier.
        field_name: Parent field name.
        num_wells: Number of wells in this macolla.
        lift_distribution: Dict of LiftType -> fraction.
        reservoir_config: Reservoir parameter ranges from field config.
        production_config: Production parameter ranges.
        template: Field template name.
    """

    name: str
    field_name: str
    num_wells: int
    lift_distribution: dict[str, float]
    reservoir_config: dict[str, Any]
    production_config: dict[str, Any]
    template: str = ""

    wells: list[WellModel] = field(default_factory=list)
    facilities: list[Facility] = field(default_factory=list)
    gateway_name: str = ""

    _rng: Generator = field(default_factory=lambda: np.random.default_rng())

    def set_rng(self, rng: Generator) -> None:
        self._rng = rng

    def initialize(self) -> None:
        """Create all wells and facilities for this macolla."""
        self.gateway_name = f"GW-{self.name}"
        self._create_wells()
        self._create_facilities()

    def _create_wells(self) -> None:
        """Create wells according to lift distribution."""
        # Determine lift type for each well
        lift_types: list[str] = []
        for lift_str, fraction in self.lift_distribution.items():
            count = max(1, round(self.num_wells * fraction))
            lift_types.extend([lift_str] * count)

        # Trim or pad to exact num_wells
        while len(lift_types) > self.num_wells:
            lift_types.pop()
        while len(lift_types) < self.num_wells:
            # Add most common type
            most_common = max(self.lift_distribution, key=self.lift_distribution.get)
            lift_types.append(most_common)

        self._rng.shuffle(lift_types)

        rc = self.reservoir_config
        pc = self.production_config

        for i, lift_str in enumerate(lift_types):
            well_name = f"{self.field_name[:2].upper()}-{self.name}-{i + 1:03d}"

            # Random reservoir parameters within ranges
            pr = self._uniform_range(rc.get("pressure_psi", [1500, 3000]))
            temp = self._uniform_range(rc.get("temperature_f", [150, 200]))
            api = self._uniform_range(rc.get("api_gravity", [10, 30]))
            visc = self._uniform_range(rc.get("viscosity_cp", [1, 5000]))
            wc = self._uniform_range(rc.get("water_cut_range", [0.2, 0.7]))
            gor = self._uniform_range(rc.get("gor_range", [100, 500]))
            avg_rate = self._uniform_range(pc.get("avg_rate_bpd", [200, 1500]))

            # Calculate bubble point and qmax from properties
            from utils.correlations import PVTCorrelations

            pb = PVTCorrelations.standing_pb(temp, api, gor)
            qmax = avg_rate * 2.5  # Approximate qmax from average rate

            reservoir = ReservoirModel(
                initial_pressure_psi=pr,
                current_pressure_psi=pr,
                temperature_f=temp,
                bubble_point_psi=min(pb, pr),
                api_gravity=api,
                gor_scf_stb=gor,
                water_cut=wc,
                water_cut_initial=wc,
                ipr_qmax_bpd=qmax,
                ipr_model="vogel" if pr <= pb * 1.2 else "darcy",
                drive_mechanism=self._pick_drive_mechanism(),
                ooip_stb=self._rng.uniform(200_000, 2_000_000),
            )

            fluid = FluidModel(
                api_gravity=api,
                reservoir_temperature_f=temp,
                gor_scf_stb=gor,
                bubble_point_psi=min(pb, pr),
            )

            # Depths with some variation
            base_depth = self._rng.uniform(4000, 12000)
            pump_depth = base_depth * 0.75

            lift_type = self._normalize_lift_type(lift_str)
            well = self._create_well_by_type(
                lift_type=lift_type,
                name=well_name,
                reservoir=reservoir,
                fluid=fluid,
                pump_depth_ft=pump_depth,
                total_depth_md_ft=base_depth * 1.05,
                total_depth_tvd_ft=base_depth,
                perforations_top_ft=base_depth * 0.9,
                perforations_bottom_ft=base_depth,
            )

            well.set_rng(np.random.default_rng(self._rng.integers(0, 2**31)))
            self.wells.append(well)

    def _create_well_by_type(
        self,
        lift_type: LiftType,
        name: str,
        reservoir: ReservoirModel,
        fluid: FluidModel,
        **kwargs: Any,
    ) -> WellModel:
        """Instantiate the correct well model subclass."""
        common = {
            "name": name,
            "field_name": self.field_name,
            "macolla_name": self.name,
            "lift_type": lift_type,
            "reservoir": reservoir,
            "fluid": fluid,
            **kwargs,
        }

        if lift_type == LiftType.ESP:
            return ESPModel(
                pump_stages=int(self._rng.uniform(100, 280)),
                design_rate_bpd=self._rng.uniform(500, 2500),
                design_head_ft=self._rng.uniform(2000, 8000),
                motor_hp=self._rng.uniform(60, 300),
                motor_voltage_v=self._rng.uniform(1000, 3500),
                motor_amperage_a=self._rng.uniform(20, 90),
                vsd_frequency_hz=self._rng.uniform(45, 65),
                **common,
            )
        elif lift_type == LiftType.SRP:
            return SRPModel(
                stroke_length_in=self._rng.uniform(100, 168),
                spm=self._rng.uniform(4, 10),
                pump_bore_in=self._rng.choice([1.5, 1.75, 2.0, 2.25, 2.5]),
                beam_load_capacity_lb=self._rng.uniform(15000, 36500),
                prime_mover_hp=self._rng.uniform(30, 75),
                **common,
            )
        elif lift_type == LiftType.GAS_LIFT:
            opt_inj = self._rng.uniform(300, 800)
            return GasLiftModel(
                num_mandrels=int(self._rng.uniform(4, 7)),
                injection_rate_mscfd=opt_inj * self._rng.uniform(0.8, 1.2),
                injection_pressure_psi=self._rng.uniform(800, 1800),
                optimal_injection_mscfd=opt_inj,
                max_injection_mscfd=opt_inj * 2,
                choke_size_64ths=int(self._rng.uniform(12, 48)),
                **common,
            )
        elif lift_type == LiftType.PCP:
            return PCPModel(
                pump_stages=int(self._rng.uniform(2, 5)),
                max_rate_bpd=self._rng.uniform(500, 3000),
                max_differential_psi=self._rng.uniform(1500, 3000),
                drive_rpm=self._rng.uniform(80, 350),
                max_torque_ftlb=self._rng.uniform(2000, 5000),
                motor_hp=self._rng.uniform(20, 100),
                sand_pct=self._rng.uniform(0, 3),
                **common,
            )
        else:
            return WellModel(**common)

    def _create_facilities(self) -> None:
        """Create surface facilities for this macolla."""
        # Default: 2 separators, 1 compressor/heater, 2 tanks
        facilities_spec = [
            ("separator", 2, {"pressure_psi": 80, "capacity_bpd": 10000}),
            ("compressor", 1, {"capacity_mscfd": 5000, "discharge_psi": 1200}),
            ("tank", 2, {"capacity_bbl": 5000}),
        ]

        for ftype, count, specs in facilities_spec:
            for j in range(count):
                fname = f"{ftype.upper()}-{self.name}-{j + 1:02d}"
                self.facilities.append(
                    Facility(
                        name=fname,
                        facility_type=ftype,
                        macolla_name=self.name,
                        specs=specs,
                    )
                )

    def _normalize_lift_type(self, lift_str: str) -> LiftType:
        """Convert config string to LiftType enum."""
        mapping = {
            "ESP": LiftType.ESP,
            "SRP": LiftType.SRP,
            "gas_lift": LiftType.GAS_LIFT,
            "PCP": LiftType.PCP,
        }
        return mapping.get(lift_str, LiftType.ESP)

    def _pick_drive_mechanism(self) -> str:
        """Pick a drive mechanism based on template."""
        if "faja" in self.template.lower():
            return "solution_gas"
        elif "lago" in self.template.lower() or "maracaibo" in self.template.lower():
            return self._rng.choice(["water_drive", "solution_gas"], p=[0.7, 0.3])
        else:
            return self._rng.choice(["gas_cap", "water_drive", "solution_gas"], p=[0.4, 0.3, 0.3])

    def _uniform_range(self, range_val: list[float] | float) -> float:
        """Sample uniformly from a [min, max] range or return scalar."""
        if isinstance(range_val, list) and len(range_val) == 2:
            return float(self._rng.uniform(range_val[0], range_val[1]))
        return float(range_val) if not isinstance(range_val, list) else float(range_val[0])

    def get_aggregate_production(self) -> dict[str, float]:
        """Sum production across all wells."""
        total_oil = sum(w.cumulative_oil_stb for w in self.wells)
        total_water = sum(w.cumulative_water_stb for w in self.wells)
        total_gas = sum(w.cumulative_gas_mscf for w in self.wells)
        active = sum(1 for w in self.wells if w.status.value == "producing")
        return {
            "total_oil_stb": total_oil,
            "total_water_stb": total_water,
            "total_gas_mscf": total_gas,
            "active_wells": active,
            "total_wells": len(self.wells),
        }
