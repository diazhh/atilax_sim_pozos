"""Event generator for well operations.

Generates operational events like workovers, well shutdowns,
pump changes, and chemical treatments with realistic timing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from numpy.random import Generator

from models.well_model import WellModel, WellStatus

logger = logging.getLogger(__name__)


@dataclass
class WellEvent:
    """A discrete well event."""

    event_type: str
    well_name: str
    start_time: datetime
    duration_days: float
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class EventGenerator:
    """Generates random operational events for wells.

    Events include workovers, pump replacements, electrical outages,
    chemical treatments, and shut-in periods.
    """

    # Event types with probabilities and durations
    EVENT_TYPES = {
        "workover": {
            "prob_per_well_per_year": 0.15,
            "duration_days": (7, 30),
            "description": "Workover - pulling and replacing completion",
        },
        "pump_replacement": {
            "prob_per_well_per_year": 0.25,
            "duration_days": (3, 14),
            "description": "Pump replacement",
        },
        "electrical_outage": {
            "prob_per_well_per_year": 2.0,
            "duration_days": (0.1, 3),
            "description": "Electrical outage (typical Venezuela)",
        },
        "chemical_treatment": {
            "prob_per_well_per_year": 4.0,
            "duration_days": (0.5, 2),
            "description": "Chemical treatment (inhibitor, dispersant)",
        },
        "scheduled_shutdown": {
            "prob_per_well_per_year": 1.0,
            "duration_days": (1, 5),
            "description": "Scheduled maintenance shutdown",
        },
    }

    def __init__(self, rng: Generator | None = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.scheduled_events: list[WellEvent] = []
        self.active_events: list[WellEvent] = []
        self.completed_events: list[WellEvent] = []

    def schedule_events_for_period(
        self,
        wells: list[WellModel],
        start_date: datetime,
        end_date: datetime,
    ) -> list[WellEvent]:
        """Pre-schedule events for a simulation period.

        Args:
            wells: All wells to generate events for.
            start_date: Simulation start.
            end_date: Simulation end.

        Returns:
            List of scheduled events.
        """
        period_days = (end_date - start_date).total_seconds() / 86400

        for well in wells:
            for event_type, params in self.EVENT_TYPES.items():
                prob_per_day = params["prob_per_well_per_year"] / 365
                # Poisson process: number of events in period
                expected = prob_per_day * period_days
                n_events = self.rng.poisson(expected)

                for _ in range(n_events):
                    offset_days = self.rng.uniform(0, period_days)
                    event_time = start_date + timedelta(days=offset_days)
                    dur_min, dur_max = params["duration_days"]
                    duration = self.rng.uniform(dur_min, dur_max)

                    event = WellEvent(
                        event_type=event_type,
                        well_name=well.name,
                        start_time=event_time,
                        duration_days=duration,
                        description=params["description"],
                    )
                    self.scheduled_events.append(event)

        # Sort by start time
        self.scheduled_events.sort(key=lambda e: e.start_time)
        logger.info("Scheduled %d events for %d wells", len(self.scheduled_events), len(wells))
        return self.scheduled_events

    def check_events(
        self,
        wells: dict[str, WellModel],
        current_time: datetime,
    ) -> list[WellEvent]:
        """Check and activate/deactivate events at current_time.

        Args:
            wells: Dict of well_name -> WellModel.
            current_time: Current simulation time.

        Returns:
            List of newly activated events.
        """
        newly_active: list[WellEvent] = []

        # Activate pending events
        pending = [e for e in self.scheduled_events if e.start_time <= current_time]
        for event in pending:
            self.scheduled_events.remove(event)
            self.active_events.append(event)
            newly_active.append(event)

            well = wells.get(event.well_name)
            if well:
                if event.event_type in ("workover", "pump_replacement", "scheduled_shutdown"):
                    well.status = WellStatus.WORKOVER
                elif event.event_type == "electrical_outage":
                    well.status = WellStatus.SHUT_IN
                logger.info(
                    "Event started: %s on %s (duration: %.1f days)",
                    event.event_type, event.well_name, event.duration_days,
                )

        # Complete expired events
        expired = []
        for event in self.active_events:
            end_time = event.start_time + timedelta(days=event.duration_days)
            if current_time >= end_time:
                expired.append(event)
                well = wells.get(event.well_name)
                if well:
                    well.status = WellStatus.PRODUCING
                    logger.info("Event ended: %s on %s", event.event_type, event.well_name)

        for event in expired:
            self.active_events.remove(event)
            self.completed_events.append(event)

        return newly_active
