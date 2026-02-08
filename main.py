#!/usr/bin/env python3
"""Atilax Well Simulator - CLI entry point.

Simulates Venezuelan oilfield operations and sends data to ThingsBoard PE.

Usage:
    python main.py create --config config/default_config.yaml
    python main.py simulate --config config/default_config.yaml --mode realtime
    python main.py simulate --config config/default_config.yaml --mode historical --days 365
    python main.py delete --config config/default_config.yaml
    python main.py status --config config/default_config.yaml
"""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import os
import signal
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from models.field_model import FieldModel
from tb_client.api_client import TBApiClient
from tb_client.entity_creator import EntityCreator
from tb_client.telemetry_sender import TelemetrySender
from generators.telemetry_generator import TelemetryGenerator
from generators.anomaly_injector import AnomalyInjector

logger = logging.getLogger("atilax")


# ── Configuration ────────────────────────────────────────────────────────


def load_config(config_path: str) -> dict[str, Any]:
    """Load and resolve YAML configuration."""
    path = Path(config_path)
    if not path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    with open(path) as f:
        config = yaml.safe_load(f)

    # Resolve environment variables
    tb = config.get("thingsboard", {})
    for key in ("password", "username", "url"):
        val = tb.get(key, "")
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            resolved = os.environ.get(env_var)
            if not resolved:
                logger.error("Environment variable %s not set", env_var)
                sys.exit(1)
            tb[key] = resolved

    return config


def setup_logging(verbose: bool = False) -> None:
    """Configure rotating log output."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, stream=sys.stdout)

    # Also log to file
    file_handler = logging.handlers.RotatingFileHandler(
        "atilax_simulator.log", maxBytes=10_000_000, backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logging.getLogger().addHandler(file_handler)


# ── Initialization ───────────────────────────────────────────────────────


def create_tb_client(config: dict) -> TBApiClient:
    """Create and authenticate ThingsBoard API client."""
    tb = config["thingsboard"]
    client = TBApiClient(tb["url"], tb["username"], tb["password"])
    client.login()
    return client


def create_field_models(config: dict) -> list[FieldModel]:
    """Create field models from configuration."""
    seed = config.get("simulation", {}).get("seed", 42)
    fields: list[FieldModel] = []

    for i, field_cfg in enumerate(config.get("fields", [])):
        field_seed = seed + i * 1000
        field_model = FieldModel.from_config(field_cfg, seed=field_seed)
        field_model.initialize()
        fields.append(field_model)
        logger.info(
            "Initialized field '%s': %d macollas, %d wells",
            field_model.name,
            len(field_model.macollas),
            len(field_model.get_all_wells()),
        )

    return fields


# ── Commands ─────────────────────────────────────────────────────────────


def cmd_create(config: dict) -> None:
    """Create all entities in ThingsBoard."""
    client = create_tb_client(config)
    fields = create_field_models(config)
    creator = EntityCreator(client)

    logger.info("Creating entities in ThingsBoard...")
    creator.create_all(fields)

    # Print summary
    total_wells = sum(len(f.get_all_wells()) for f in fields)
    total_macollas = sum(len(f.macollas) for f in fields)
    logger.info(
        "Creation complete: %d fields, %d macollas, %d wells, %d total entities",
        len(fields), total_macollas, total_wells, len(creator.registry),
    )


def cmd_simulate(config: dict, mode: str, days: int) -> None:
    """Run simulation in realtime or historical mode."""
    client = create_tb_client(config)
    fields = create_field_models(config)
    creator = EntityCreator(client)

    # Register existing entities (idempotent create)
    logger.info("Registering entities...")
    creator.create_all(fields)

    sim_cfg = config.get("simulation", {})
    anomaly_cfg = config.get("anomalies", {})

    # Telemetry sender
    use_mqtt = mode == "realtime"
    sender = TelemetrySender(client, use_mqtt=use_mqtt)

    # Anomaly injector
    injector = None
    if anomaly_cfg.get("enabled", False):
        injector = AnomalyInjector(
            probability_per_well_per_day=anomaly_cfg.get("probability_per_well_per_day", 0.02),
            enabled_types=anomaly_cfg.get("types"),
            rng=np.random.default_rng(sim_cfg.get("seed", 42)),
        )

    generator = TelemetryGenerator(fields, creator, sender, injector)

    # Handle graceful shutdown
    def signal_handler(sig: int, frame: Any) -> None:
        logger.info("Shutdown signal received, stopping...")
        generator.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if mode == "realtime":
        interval = sim_cfg.get("realtime_interval_sec", 30)
        acceleration = sim_cfg.get("time_acceleration", 1)
        logger.info(
            "Starting REALTIME simulation: interval=%ds, acceleration=%dx",
            interval, acceleration,
        )
        generator.run_realtime(
            interval_sec=interval,
            time_acceleration=acceleration,
        )
    else:
        historical_days = days or sim_cfg.get("historical_days", 365)
        samples_per_day = max(1, 86400 // sim_cfg.get("realtime_interval_sec", 30))
        # Cap at 48 samples/day for historical to keep data manageable
        samples_per_day = min(samples_per_day, 48)
        logger.info(
            "Starting HISTORICAL simulation: %d days, %d samples/day",
            historical_days, samples_per_day,
        )
        generator.run_historical(days=historical_days, samples_per_day=samples_per_day)

    stats = sender.get_stats()
    logger.info("Simulation complete. Messages sent: %d, Errors: %d", stats["messages_sent"], stats["errors"])


def cmd_delete(config: dict) -> None:
    """Delete all simulator entities from ThingsBoard."""
    client = create_tb_client(config)
    fields = create_field_models(config)
    creator = EntityCreator(client)

    # First register (find) all entities
    creator.create_all(fields)

    logger.info("Deleting all entities...")
    creator.delete_all(fields)
    logger.info("Deletion complete")


def cmd_status(config: dict) -> None:
    """Show status of simulation entities."""
    fields = create_field_models(config)

    print("\n=== Atilax Well Simulator - Status ===\n")
    total_wells = 0

    for field_model in fields:
        summary = field_model.get_summary()
        wells = summary["total_wells"]
        total_wells += wells

        print(f"Field: {summary['field_name']} (template: {summary['template']})")
        print(f"  Macollas: {summary['num_macollas']}")
        print(f"  Total wells: {wells}")
        print(f"  By lift type: {summary['wells_by_lift_type']}")

        for mac in summary["macollas"]:
            print(f"    {mac['name']}: {mac['num_wells']} wells, {mac['num_facilities']} facilities")

        print()

    print(f"TOTAL: {len(fields)} fields, {total_wells} wells")

    # Try TB connection
    try:
        client = create_tb_client(config)
        print("\nThingsBoard connection: OK")
    except Exception as e:
        print(f"\nThingsBoard connection: FAILED ({e})")


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atilax Well Simulator - Venezuelan oilfield simulation for ThingsBoard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py create --config config/default_config.yaml
  python main.py simulate --config config/default_config.yaml --mode realtime
  python main.py simulate --config config/default_config.yaml --mode historical --days 365
  python main.py delete --config config/default_config.yaml
  python main.py status --config config/default_config.yaml
        """,
    )

    parser.add_argument(
        "command",
        choices=["create", "simulate", "delete", "status"],
        help="Command to execute",
    )
    parser.add_argument(
        "--config", "-c",
        default="config/default_config.yaml",
        help="Path to YAML configuration file (default: config/default_config.yaml)",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["realtime", "historical"],
        default="realtime",
        help="Simulation mode (default: realtime)",
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=0,
        help="Days of historical data to generate (default: from config)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    config = load_config(args.config)

    if args.command == "create":
        cmd_create(config)
    elif args.command == "simulate":
        cmd_simulate(config, args.mode, args.days)
    elif args.command == "delete":
        cmd_delete(config)
    elif args.command == "status":
        cmd_status(config)


if __name__ == "__main__":
    main()
