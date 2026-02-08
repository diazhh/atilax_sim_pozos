"""Entity creator for ThingsBoard.

Creates the complete hierarchy of assets, devices, relations,
and attributes from the simulation model. Idempotent: skips
entities that already exist.
"""

from __future__ import annotations

import logging
from typing import Any

from tb_client.api_client import TBApiClient
from models.field_model import FieldModel
from models.macolla_model import MacollaModel, Facility
from models.well_model import WellModel

logger = logging.getLogger(__name__)


class EntityCreator:
    """Creates ThingsBoard entities from field models.

    Maintains a registry of created entity IDs for relation
    building and telemetry sending.
    """

    def __init__(self, client: TBApiClient) -> None:
        self.client = client
        # Registry: name -> {"id": str, "type": str (ASSET|DEVICE)}
        self.registry: dict[str, dict[str, str]] = {}
        # Device credentials: device_name -> access_token
        self.device_tokens: dict[str, str] = {}

    def create_all(self, fields: list[FieldModel]) -> None:
        """Create all entities for all fields."""
        self._ensure_device_profiles()

        for field_model in fields:
            self._create_field(field_model)

        logger.info(
            "Entity creation complete: %d entities registered", len(self.registry)
        )

    def delete_all(self, fields: list[FieldModel]) -> None:
        """Delete all entities for all fields (reverse order)."""
        for field_model in fields:
            self._delete_field(field_model)
        self.registry.clear()
        self.device_tokens.clear()
        logger.info("All entities deleted")

    # ── Device Profiles ──────────────────────────────────────────────────

    def _ensure_device_profiles(self) -> None:
        """Create device profiles if they don't exist."""
        profiles = [
            ("rtu_esp", "RTU for ESP wells"),
            ("rtu_srp", "RTU for SRP wells"),
            ("rtu_gaslift", "RTU for Gas Lift wells"),
            ("rtu_pcp", "RTU for PCP wells"),
            ("downhole_gauge", "Downhole pressure/temperature gauge"),
            ("multiphase_meter", "Multiphase flow meter"),
            ("iot_gateway", "IoT gateway per macolla"),
        ]
        for name, desc in profiles:
            existing = self.client.find_device_profile_by_name(name)
            if existing:
                logger.debug("Device profile '%s' already exists", name)
            else:
                self.client.create_device_profile(name, desc)
                logger.info("Created device profile: %s", name)

    # ── Field ────────────────────────────────────────────────────────────

    def _create_field(self, field_model: FieldModel) -> None:
        """Create field asset and all children."""
        field_id = self._create_or_get_asset(field_model.name, "field")

        for macolla in field_model.macollas:
            macolla_id = self._create_macolla(macolla)
            # Field -> Macolla relation
            self.client.create_relation("ASSET", field_id, "ASSET", macolla_id, "Contains")

    def _delete_field(self, field_model: FieldModel) -> None:
        """Delete field and all children."""
        for macolla in field_model.macollas:
            self._delete_macolla(macolla)
        self._delete_entity(field_model.name, "ASSET")

    # ── Macolla ──────────────────────────────────────────────────────────

    def _create_macolla(self, macolla: MacollaModel) -> str:
        """Create macolla asset, its wells, facilities, and gateway."""
        macolla_id = self._create_or_get_asset(macolla.name, "macolla")

        # Gateway device
        gw_id = self._create_or_get_device(macolla.gateway_name, "iot_gateway")
        self.client.create_relation("ASSET", macolla_id, "DEVICE", gw_id, "Contains")

        # Facilities
        for facility in macolla.facilities:
            fac_id = self._create_or_get_asset(facility.name, "facility")
            self.client.create_relation("ASSET", macolla_id, "ASSET", fac_id, "Contains")
            self.client.set_server_attributes("ASSET", fac_id, facility.get_attributes())

        # Wells
        for well in macolla.wells:
            well_id = self._create_well(well)
            self.client.create_relation("ASSET", macolla_id, "ASSET", well_id, "Contains")

            # Well -> Facility "Uses" relation (first separator)
            if macolla.facilities:
                sep = next(
                    (f for f in macolla.facilities if f.facility_type == "separator"),
                    macolla.facilities[0],
                )
                sep_info = self.registry.get(sep.name)
                if sep_info:
                    self.client.create_relation(
                        "ASSET", well_id, "ASSET", sep_info["id"], "Uses"
                    )

        return macolla_id

    def _delete_macolla(self, macolla: MacollaModel) -> None:
        """Delete macolla and children."""
        for well in macolla.wells:
            self._delete_well(well)
        for facility in macolla.facilities:
            self._delete_entity(facility.name, "ASSET")
        self._delete_entity(macolla.gateway_name, "DEVICE")
        self._delete_entity(macolla.name, "ASSET")

    # ── Well ─────────────────────────────────────────────────────────────

    def _create_well(self, well: WellModel) -> str:
        """Create well asset and its RTU device."""
        well_id = self._create_or_get_asset(well.name, "well")

        # Set server attributes
        attrs = well.get_static_attributes()
        self.client.set_server_attributes("ASSET", well_id, attrs)

        # RTU device
        rtu_name = f"RTU-{well.name}"
        device_type = well.get_device_type()
        rtu_id = self._create_or_get_device(rtu_name, device_type)
        self.client.create_relation("ASSET", well_id, "DEVICE", rtu_id, "Contains")

        # Optionally add downhole gauge (30% of ESP wells)
        if well.lift_type.value == "ESP" and hash(well.name) % 10 < 3:
            dh_name = f"DH-{well.name}"
            dh_id = self._create_or_get_device(dh_name, "downhole_gauge")
            self.client.create_relation("ASSET", well_id, "DEVICE", dh_id, "Contains")

        # Optionally add multiphase meter (20% of wells)
        if hash(well.name) % 10 < 2:
            mm_name = f"MM-{well.name}"
            mm_id = self._create_or_get_device(mm_name, "multiphase_meter")
            self.client.create_relation("ASSET", well_id, "DEVICE", mm_id, "Contains")

        logger.info("Created well %s (%s) with RTU %s", well.name, well.lift_type.value, rtu_name)
        return well_id

    def _delete_well(self, well: WellModel) -> None:
        """Delete well and its devices."""
        rtu_name = f"RTU-{well.name}"
        dh_name = f"DH-{well.name}"
        mm_name = f"MM-{well.name}"
        self._delete_entity(rtu_name, "DEVICE")
        self._delete_entity(dh_name, "DEVICE")
        self._delete_entity(mm_name, "DEVICE")
        self._delete_entity(well.name, "ASSET")

    # ── Helpers ──────────────────────────────────────────────────────────

    def _create_or_get_asset(self, name: str, asset_type: str) -> str:
        """Create asset if it doesn't exist. Return entity ID."""
        if name in self.registry:
            return self.registry[name]["id"]

        existing = self.client.find_asset_by_name(name)
        if existing:
            eid = existing["id"]["id"]
            self.registry[name] = {"id": eid, "type": "ASSET"}
            logger.debug("Asset '%s' already exists (id=%s)", name, eid)
            return eid

        result = self.client.create_asset(name, asset_type)
        eid = result["id"]["id"]
        self.registry[name] = {"id": eid, "type": "ASSET"}
        logger.info("Created asset: %s (type=%s, id=%s)", name, asset_type, eid)
        return eid

    def _create_or_get_device(self, name: str, device_type: str) -> str:
        """Create device if it doesn't exist. Return entity ID and store token."""
        if name in self.registry:
            return self.registry[name]["id"]

        existing = self.client.find_device_by_name(name)
        if existing:
            eid = existing["id"]["id"]
            self.registry[name] = {"id": eid, "type": "DEVICE"}
            creds = self.client.get_device_credentials(eid)
            self.device_tokens[name] = creds.get("credentialsId", "")
            logger.debug("Device '%s' already exists (id=%s)", name, eid)
            return eid

        result = self.client.create_device(name, device_type)
        eid = result["id"]["id"]
        self.registry[name] = {"id": eid, "type": "DEVICE"}
        creds = self.client.get_device_credentials(eid)
        self.device_tokens[name] = creds.get("credentialsId", "")
        logger.info("Created device: %s (type=%s, id=%s)", name, device_type, eid)
        return eid

    def _delete_entity(self, name: str, entity_type: str) -> None:
        """Delete entity by name if it exists."""
        info = self.registry.pop(name, None)
        if not info:
            return
        try:
            if entity_type == "ASSET":
                self.client.delete_asset(info["id"])
            else:
                self.client.delete_device(info["id"])
            self.device_tokens.pop(name, None)
            logger.info("Deleted %s: %s", entity_type, name)
        except Exception as e:
            logger.warning("Failed to delete %s '%s': %s", entity_type, name, e)

    def get_device_id(self, device_name: str) -> str | None:
        """Get the TB entity ID for a device by name."""
        info = self.registry.get(device_name)
        return info["id"] if info else None

    def get_device_token(self, device_name: str) -> str | None:
        """Get the MQTT access token for a device."""
        return self.device_tokens.get(device_name)
