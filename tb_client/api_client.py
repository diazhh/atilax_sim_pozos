"""ThingsBoard REST API client.

Handles authentication, token refresh, and low-level HTTP calls
to the ThingsBoard Professional Edition REST API.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class TBApiClient:
    """Low-level ThingsBoard REST API client.

    Handles JWT authentication and provides helper methods for
    common API operations (CRUD on assets, devices, relations, etc.).
    """

    def __init__(self, url: str, username: str, password: str) -> None:
        self.base_url = url.rstrip("/")
        self.username = username
        self.password = password
        self._token: str = ""
        self._refresh_token: str = ""
        self._token_expiry: float = 0
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/json"

    # ── Authentication ───────────────────────────────────────────────────

    def login(self) -> None:
        """Authenticate and obtain JWT token."""
        resp = self._session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": self.username, "password": self.password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["token"]
        self._refresh_token = data.get("refreshToken", "")
        self._token_expiry = time.time() + 850  # ~15 min minus buffer
        self._session.headers["X-Authorization"] = f"Bearer {self._token}"
        logger.info("Authenticated to ThingsBoard as %s", self.username)

    def _ensure_auth(self) -> None:
        """Re-authenticate if token is expired or missing."""
        if not self._token or time.time() > self._token_expiry:
            self.login()

    # ── Generic HTTP helpers ─────────────────────────────────────────────

    def get(self, path: str, params: dict | None = None) -> Any:
        self._ensure_auth()
        resp = self._session.get(f"{self.base_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, json_data: Any = None) -> Any:
        self._ensure_auth()
        resp = self._session.post(f"{self.base_url}{path}", json=json_data)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def delete(self, path: str) -> None:
        self._ensure_auth()
        resp = self._session.delete(f"{self.base_url}{path}")
        resp.raise_for_status()

    # ── Asset operations ─────────────────────────────────────────────────

    def create_asset(self, name: str, asset_type: str, label: str = "") -> dict:
        """Create an asset. Returns the created asset dict with id."""
        body = {
            "name": name,
            "type": asset_type,
            "label": label or name,
        }
        return self.post("/api/asset", body)

    def find_asset_by_name(self, name: str) -> dict | None:
        """Find an asset by name. Returns None if not found."""
        try:
            data = self.get("/api/tenant/assets", params={"assetName": name})
            return data if data else None
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

    def delete_asset(self, asset_id: str) -> None:
        self.delete(f"/api/asset/{asset_id}")

    # ── Device operations ────────────────────────────────────────────────

    def create_device(
        self,
        name: str,
        device_type: str,
        label: str = "",
        device_profile_id: str | None = None,
    ) -> dict:
        """Create a device. Returns created device with id and credentials."""
        body: dict[str, Any] = {
            "name": name,
            "type": device_type,
            "label": label or name,
        }
        if device_profile_id:
            body["deviceProfileId"] = {"entityType": "DEVICE_PROFILE", "id": device_profile_id}
        return self.post("/api/device", body)

    def find_device_by_name(self, name: str) -> dict | None:
        """Find a device by name."""
        try:
            data = self.get("/api/tenant/devices", params={"deviceName": name})
            return data if data else None
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

    def get_device_credentials(self, device_id: str) -> dict:
        """Get device credentials (access token)."""
        return self.get(f"/api/device/{device_id}/credentials")

    def delete_device(self, device_id: str) -> None:
        self.delete(f"/api/device/{device_id}")

    # ── Device Profile operations ────────────────────────────────────────

    def find_device_profile_by_name(self, name: str) -> dict | None:
        """Find a device profile by name."""
        profiles = self.get(
            "/api/deviceProfiles",
            params={"pageSize": 100, "page": 0, "textSearch": name},
        )
        for p in profiles.get("data", []):
            if p.get("name") == name:
                return p
        return None

    def create_device_profile(self, name: str, description: str = "") -> dict:
        """Create a device profile."""
        body = {
            "name": name,
            "description": description,
            "type": "DEFAULT",
            "transportType": "DEFAULT",
            "profileData": {
                "configuration": {"type": "DEFAULT"},
                "transportConfiguration": {"type": "DEFAULT"},
            },
        }
        return self.post("/api/deviceProfile", body)

    # ── Relations ────────────────────────────────────────────────────────

    def create_relation(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        relation_type: str = "Contains",
    ) -> None:
        """Create a relation between two entities."""
        body = {
            "from": {"entityType": from_type, "id": from_id},
            "to": {"entityType": to_type, "id": to_id},
            "type": relation_type,
            "typeGroup": "COMMON",
        }
        self.post("/api/relation", body)

    def delete_relation(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        relation_type: str = "Contains",
    ) -> None:
        self.delete(
            f"/api/relation"
            f"?fromId={from_id}&fromType={from_type}"
            f"&relationType={relation_type}&relationTypeGroup=COMMON"
            f"&toId={to_id}&toType={to_type}"
        )

    # ── Attributes ───────────────────────────────────────────────────────

    def set_server_attributes(
        self,
        entity_type: str,
        entity_id: str,
        attributes: dict[str, Any],
    ) -> None:
        """Set server-side attributes on an entity."""
        self.post(
            f"/api/plugins/telemetry/{entity_type}/{entity_id}/attributes/SERVER_SCOPE",
            attributes,
        )

    # ── Telemetry ────────────────────────────────────────────────────────

    def send_telemetry(
        self,
        entity_type: str,
        entity_id: str,
        telemetry: dict[str, Any],
        ts: int | None = None,
    ) -> None:
        """Send telemetry via REST API.

        Args:
            entity_type: "DEVICE" or "ASSET".
            entity_id: Entity UUID.
            telemetry: Key-value telemetry data.
            ts: Optional timestamp in milliseconds.
        """
        if ts:
            body: Any = {"ts": ts, "values": telemetry}
        else:
            body = telemetry
        self.post(
            f"/api/plugins/telemetry/{entity_type}/{entity_id}/timeseries/ANY",
            body,
        )

    def send_telemetry_batch(
        self,
        entity_type: str,
        entity_id: str,
        telemetry_list: list[dict[str, Any]],
    ) -> None:
        """Send multiple timestamped telemetry points.

        Each item must have {"ts": epoch_ms, "values": {...}}.
        """
        self.post(
            f"/api/plugins/telemetry/{entity_type}/{entity_id}/timeseries/ANY",
            telemetry_list,
        )

    # ── Bulk entity search ───────────────────────────────────────────────

    def get_tenant_assets(
        self,
        page_size: int = 100,
        page: int = 0,
        text_search: str = "",
        asset_type: str = "",
    ) -> dict:
        """List tenant assets with pagination."""
        params: dict[str, Any] = {"pageSize": page_size, "page": page}
        if text_search:
            params["textSearch"] = text_search
        if asset_type:
            params["type"] = asset_type
        return self.get("/api/tenant/assets", params)

    def get_tenant_devices(
        self,
        page_size: int = 100,
        page: int = 0,
        text_search: str = "",
        device_type: str = "",
    ) -> dict:
        """List tenant devices with pagination."""
        params: dict[str, Any] = {"pageSize": page_size, "page": page}
        if text_search:
            params["textSearch"] = text_search
        if device_type:
            params["type"] = device_type
        return self.get("/api/tenant/devices", params)
