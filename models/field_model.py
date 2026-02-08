"""Field (campo petrolero) model.

Top-level entity that contains macollas, manages initialization
from config, and provides field-level aggregate data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.random import Generator

from models.macolla_model import MacollaModel


@dataclass
class FieldModel:
    """Petroleum field model containing multiple macollas.

    Attributes:
        name: Field name (e.g., "Campo Boscán").
        template: Field template identifier.
        num_macollas: Number of macollas.
        wells_per_macolla: List of well counts per macolla.
        lift_distribution: Lift type fractions.
        reservoir_config: Reservoir parameter ranges.
        production_config: Production parameter ranges.
    """

    name: str
    template: str
    num_macollas: int
    wells_per_macolla: list[int]
    lift_distribution: dict[str, float]
    reservoir_config: dict[str, Any]
    production_config: dict[str, Any]

    macollas: list[MacollaModel] = field(default_factory=list)
    _rng: Generator = field(default_factory=lambda: np.random.default_rng())

    def set_rng(self, rng: Generator) -> None:
        self._rng = rng

    @classmethod
    def from_config(cls, field_cfg: dict[str, Any], seed: int | None = None) -> "FieldModel":
        """Create a FieldModel from a config dict (one entry in the 'fields' list)."""
        rng = np.random.default_rng(seed)

        model = cls(
            name=field_cfg["name"],
            template=field_cfg.get("template", ""),
            num_macollas=field_cfg.get("num_macollas", 1),
            wells_per_macolla=field_cfg.get("wells_per_macolla", [10]),
            lift_distribution=field_cfg.get("lift_distribution", {"ESP": 1.0}),
            reservoir_config=field_cfg.get("reservoir", {}),
            production_config=field_cfg.get("production", {}),
        )
        model.set_rng(rng)
        return model

    def initialize(self) -> None:
        """Create all macollas and their wells."""
        # Pad wells_per_macolla if needed
        wpm = list(self.wells_per_macolla)
        while len(wpm) < self.num_macollas:
            wpm.append(wpm[-1] if wpm else 10)

        field_prefix = self.name.split()[-1][:3].upper() if self.name else "FLD"

        for i in range(self.num_macollas):
            macolla_name = f"MAC-{field_prefix}-{i + 1:02d}"

            macolla = MacollaModel(
                name=macolla_name,
                field_name=self.name,
                num_wells=wpm[i],
                lift_distribution=self.lift_distribution,
                reservoir_config=self.reservoir_config,
                production_config=self.production_config,
                template=self.template,
            )
            macolla.set_rng(np.random.default_rng(self._rng.integers(0, 2**31)))
            macolla.initialize()
            self.macollas.append(macolla)

    def get_all_wells(self) -> list:
        """Flat list of all wells across all macollas."""
        wells = []
        for m in self.macollas:
            wells.extend(m.wells)
        return wells

    def get_summary(self) -> dict[str, Any]:
        """Field-level summary statistics."""
        all_wells = self.get_all_wells()
        by_lift: dict[str, int] = {}
        for w in all_wells:
            lt = w.lift_type.value
            by_lift[lt] = by_lift.get(lt, 0) + 1

        return {
            "field_name": self.name,
            "template": self.template,
            "num_macollas": len(self.macollas),
            "total_wells": len(all_wells),
            "wells_by_lift_type": by_lift,
            "macollas": [
                {
                    "name": m.name,
                    "num_wells": len(m.wells),
                    "num_facilities": len(m.facilities),
                    "gateway": m.gateway_name,
                }
                for m in self.macollas
            ],
        }
