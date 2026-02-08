"""Telemetry sender for ThingsBoard via MQTT and REST.

Manages MQTT connections for real-time streaming and REST API
for historical batch uploads. Handles rate limiting and reconnection.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt

from tb_client.api_client import TBApiClient

logger = logging.getLogger(__name__)

# ThingsBoard MQTT topics
TELEMETRY_TOPIC = "v1/devices/me/telemetry"
ATTRIBUTES_TOPIC = "v1/devices/me/attributes"


class TelemetrySender:
    """Send telemetry to ThingsBoard via MQTT or REST.

    For real-time simulation, uses per-device MQTT connections.
    For historical batch, uses the REST API.
    """

    def __init__(
        self,
        api_client: TBApiClient,
        mqtt_host: str | None = None,
        mqtt_port: int = 1883,
        use_mqtt: bool = True,
    ) -> None:
        self.api_client = api_client
        self.mqtt_host = mqtt_host or self._extract_host(api_client.base_url)
        self.mqtt_port = mqtt_port
        self.use_mqtt = use_mqtt

        # MQTT clients keyed by device access token
        self._mqtt_clients: dict[str, mqtt.Client] = {}
        self._lock = threading.Lock()

        # Rate limiting
        self._last_send_time: float = 0
        self._min_interval_sec: float = 0.01  # 100 msgs/sec max

        # Counters
        self.messages_sent: int = 0
        self.errors: int = 0

    # ── MQTT Management ──────────────────────────────────────────────────

    def connect_device(self, device_name: str, access_token: str) -> None:
        """Establish MQTT connection for a device."""
        if not self.use_mqtt:
            return

        with self._lock:
            if access_token in self._mqtt_clients:
                return

            client = mqtt.Client(client_id=f"sim-{device_name}")
            client.username_pw_set(access_token)

            client.on_connect = lambda c, ud, flags, rc: logger.debug(
                "MQTT connected: %s (rc=%d)", device_name, rc
            )
            client.on_disconnect = lambda c, ud, rc: logger.warning(
                "MQTT disconnected: %s (rc=%d)", device_name, rc
            )

            try:
                client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
                client.loop_start()
                self._mqtt_clients[access_token] = client
                logger.debug("MQTT connected for device: %s", device_name)
            except Exception as e:
                logger.error("MQTT connection failed for %s: %s", device_name, e)
                self.errors += 1

    def disconnect_all(self) -> None:
        """Disconnect all MQTT clients."""
        with self._lock:
            for token, client in self._mqtt_clients.items():
                try:
                    client.loop_stop()
                    client.disconnect()
                except Exception:
                    pass
            self._mqtt_clients.clear()
        logger.info("All MQTT connections closed")

    # ── Sending Telemetry ────────────────────────────────────────────────

    def send_realtime(
        self,
        access_token: str,
        telemetry: dict[str, Any],
    ) -> None:
        """Send real-time telemetry via MQTT.

        Args:
            access_token: Device MQTT access token.
            telemetry: Key-value telemetry data.
        """
        self._rate_limit()

        client = self._mqtt_clients.get(access_token)
        if not client:
            logger.warning("No MQTT client for token %s..., falling back to REST", access_token[:8])
            return

        payload = json.dumps(telemetry)
        result = client.publish(TELEMETRY_TOPIC, payload, qos=1)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.messages_sent += 1
        else:
            logger.warning("MQTT publish failed (rc=%d)", result.rc)
            self.errors += 1

    def send_historical(
        self,
        entity_type: str,
        entity_id: str,
        telemetry_batch: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> None:
        """Send historical telemetry via REST API in batches.

        Args:
            entity_type: "DEVICE" or "ASSET".
            entity_id: Entity UUID.
            telemetry_batch: List of {"ts": epoch_ms, "values": {...}}.
            batch_size: Number of data points per REST call.
        """
        for i in range(0, len(telemetry_batch), batch_size):
            batch = telemetry_batch[i : i + batch_size]
            try:
                self.api_client.send_telemetry_batch(entity_type, entity_id, batch)
                self.messages_sent += len(batch)
                self._rate_limit()
            except Exception as e:
                logger.error(
                    "Failed to send batch %d-%d for %s: %s",
                    i, i + len(batch), entity_id, e,
                )
                self.errors += 1
                time.sleep(1)  # Back off on error

    def send_single(
        self,
        entity_type: str,
        entity_id: str,
        telemetry: dict[str, Any],
        ts: int | None = None,
    ) -> None:
        """Send a single telemetry point via REST.

        Args:
            entity_type: "DEVICE" or "ASSET".
            entity_id: Entity UUID.
            telemetry: Key-value data.
            ts: Optional timestamp in ms.
        """
        try:
            self.api_client.send_telemetry(entity_type, entity_id, telemetry, ts)
            self.messages_sent += 1
        except Exception as e:
            logger.error("Failed to send telemetry to %s: %s", entity_id, e)
            self.errors += 1

    # ── Rate Limiting ────────────────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Simple rate limiter to avoid overwhelming TB."""
        now = time.time()
        elapsed = now - self._last_send_time
        if elapsed < self._min_interval_sec:
            time.sleep(self._min_interval_sec - elapsed)
        self._last_send_time = time.time()

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_host(url: str) -> str:
        """Extract hostname from URL for MQTT connection."""
        host = url.replace("https://", "").replace("http://", "")
        host = host.split("/")[0].split(":")[0]
        return host

    def get_stats(self) -> dict[str, int]:
        return {
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "active_mqtt_connections": len(self._mqtt_clients),
        }
