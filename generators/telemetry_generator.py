"""Telemetry generator orchestrating well model steps.

Coordinates time stepping across all wells, applies scenarios,
and feeds data to the telemetry sender.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

from models.field_model import FieldModel
from models.well_model import WellModel
from tb_client.entity_creator import EntityCreator
from tb_client.telemetry_sender import TelemetrySender

logger = logging.getLogger(__name__)


class TelemetryGenerator:
    """Generates and sends telemetry for all wells.

    Supports both real-time (continuous streaming) and historical
    (batch backfill) modes.
    """

    def __init__(
        self,
        fields: list[FieldModel],
        entity_creator: EntityCreator,
        telemetry_sender: TelemetrySender,
        anomaly_injector: Any = None,
    ) -> None:
        self.fields = fields
        self.entity_creator = entity_creator
        self.sender = telemetry_sender
        self.anomaly_injector = anomaly_injector
        self._running = False

    def run_realtime(
        self,
        interval_sec: float = 30,
        time_acceleration: float = 1.0,
    ) -> None:
        """Run continuous real-time simulation.

        Args:
            interval_sec: Seconds between telemetry samples.
            time_acceleration: Sim time multiplier (60 = 1 min real = 1 hr sim).
        """
        self._running = True
        sim_time = datetime.utcnow()
        dt_days = (interval_sec * time_acceleration) / 86400.0

        # Connect MQTT for all RTU devices
        self._connect_mqtt_devices()

        logger.info(
            "Starting real-time simulation: interval=%ds, acceleration=%.0fx, dt=%.4f days",
            interval_sec, time_acceleration, dt_days,
        )

        cycle = 0
        while self._running:
            cycle_start = time.time()

            for field_model in self.fields:
                for well in field_model.get_all_wells():
                    self._step_and_send_well(well, dt_days, sim_time)

            sim_time += timedelta(days=dt_days)
            cycle += 1

            if cycle % 10 == 0:
                stats = self.sender.get_stats()
                logger.info(
                    "Cycle %d | Sim time: %s | Sent: %d | Errors: %d",
                    cycle, sim_time.isoformat(), stats["messages_sent"], stats["errors"],
                )

            # Sleep for the remaining interval
            elapsed = time.time() - cycle_start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.sender.disconnect_all()
        logger.info("Real-time simulation stopped")

    def run_historical(
        self,
        days: int = 365,
        samples_per_day: int = 48,
    ) -> None:
        """Generate historical data in batch mode.

        Args:
            days: Number of days of history to generate.
            samples_per_day: Number of telemetry samples per day.
        """
        self._running = True
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        dt_days = 1.0 / samples_per_day
        interval = timedelta(days=dt_days)

        total_steps = days * samples_per_day
        logger.info(
            "Starting historical generation: %d days, %d samples/day, %d total steps",
            days, samples_per_day, total_steps,
        )

        for field_model in self.fields:
            for well in field_model.get_all_wells():
                if not self._running:
                    break
                self._generate_well_history(
                    well, start_time, end_time, dt_days, interval
                )

        logger.info("Historical generation complete")

    def stop(self) -> None:
        """Signal the generator to stop."""
        self._running = False

    # ── Internal ─────────────────────────────────────────────────────────

    def _step_and_send_well(
        self,
        well: WellModel,
        dt_days: float,
        sim_time: datetime,
    ) -> None:
        """Step one well and send telemetry."""
        # Apply anomalies if injector is active
        if self.anomaly_injector:
            self.anomaly_injector.maybe_inject(well, dt_days)

        telemetry = well.step(dt_days, sim_time)
        if not telemetry:
            return

        rtu_name = f"RTU-{well.name}"
        token = self.entity_creator.get_device_token(rtu_name)

        if token and self.sender.use_mqtt:
            self.sender.send_realtime(token, telemetry)
        else:
            device_id = self.entity_creator.get_device_id(rtu_name)
            if device_id:
                ts_ms = int(sim_time.timestamp() * 1000)
                self.sender.send_single("DEVICE", device_id, telemetry, ts=ts_ms)

    def _generate_well_history(
        self,
        well: WellModel,
        start_time: datetime,
        end_time: datetime,
        dt_days: float,
        interval: timedelta,
    ) -> None:
        """Generate and upload historical data for one well."""
        rtu_name = f"RTU-{well.name}"
        device_id = self.entity_creator.get_device_id(rtu_name)
        if not device_id:
            logger.warning("No device ID for %s, skipping history", rtu_name)
            return

        batch: list[dict[str, Any]] = []
        current_time = start_time

        while current_time < end_time and self._running:
            if self.anomaly_injector:
                self.anomaly_injector.maybe_inject(well, dt_days)

            telemetry = well.step(dt_days, current_time)
            if telemetry:
                ts_ms = int(current_time.timestamp() * 1000)
                batch.append({"ts": ts_ms, "values": telemetry})

            # Send in chunks to avoid memory issues
            if len(batch) >= 500:
                self.sender.send_historical("DEVICE", device_id, batch)
                batch.clear()

            current_time += interval

        # Send remaining
        if batch:
            self.sender.send_historical("DEVICE", device_id, batch)

        logger.info("Generated history for %s: %s to %s", well.name, start_time.date(), end_time.date())

    def _connect_mqtt_devices(self) -> None:
        """Connect MQTT for all RTU devices."""
        for field_model in self.fields:
            for well in field_model.get_all_wells():
                rtu_name = f"RTU-{well.name}"
                token = self.entity_creator.get_device_token(rtu_name)
                if token:
                    self.sender.connect_device(rtu_name, token)
