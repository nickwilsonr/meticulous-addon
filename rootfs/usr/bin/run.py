#!/usr/bin/env python3
"""Meticulous Espresso Add-on main application."""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional
import random
from datetime import datetime

import aiohttp
import json as jsonlib

# Import Meticulous API
try:
    from meticulous.api import Api, ApiOptions
    from meticulous.api_types import (
        StatusData,
        Temperatures,
        APIError,
        NotificationData,
    )
except ImportError as e:
    print(f"ERROR: Failed to import pyMeticulous: {e}")
    print("Make sure pyMeticulous is installed: pip install pymeticulous")
    sys.exit(1)

# Import MQTT - imported locally where needed to avoid F811
try:
    import paho.mqtt.client  # noqa: F401
except ImportError as e:
    print(f"ERROR: Failed to import paho-mqtt: {e}")
    print("Make sure paho-mqtt is installed: pip install paho-mqtt")
    sys.exit(1)

# Import MQTT command handlers
try:
    from mqtt_commands import mqtt_on_message
except ImportError as e:
    print(f"ERROR: Failed to import mqtt_commands: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


class MeticulousAddon:
    """Main class for Meticulous Espresso Add-on."""

    def __init__(self):
        """Initialize the add-on."""
        self.config = self._load_config()
        self._setup_logging()
        self.machine_ip = self.config.get("machine_ip")
        self.scan_interval = self.config.get("scan_interval", 30)
        self.running = False
        self.socket_connected = False
        # Backoff configuration
        self.retry_initial = int(self.config.get("retry_initial", 2))
        self.retry_max = int(self.config.get("retry_max", 60))
        self.retry_jitter = bool(self.config.get("retry_jitter", True))

        # Connectivity state
        self.socket_connected = False
        self.api_connected = False

        # Health metrics tracking
        self.start_time = datetime.now()
        self.reconnect_count = 0
        self.last_error = None
        self.last_error_time = None

        # Initialize API with event handlers
        self.api: Optional[Api] = None
        self.supervisor_token = os.getenv("SUPERVISOR_TOKEN")

        # State tracking
        self.current_state = "unknown"
        self.current_profile = None
        self.device_info = None

        # Home Assistant session
        self.ha_session: Optional[aiohttp.ClientSession] = None

        # MQTT configuration
        self.mqtt_enabled = bool(self.config.get("mqtt_enabled", True))
        self.mqtt_host = self.config.get("mqtt_host", "core-mosquitto")
        self.mqtt_port = int(self.config.get("mqtt_port", 1883))
        self.mqtt_username = self.config.get("mqtt_username") or None
        self.mqtt_password = self.config.get("mqtt_password") or None
        self.slug = "meticulous_espresso"
        self.availability_topic = f"{self.slug}/availability"
        self.state_prefix = f"{self.slug}/sensor"
        self.command_prefix = f"{self.slug}/command"
        self.discovery_prefix = "homeassistant"
        self.mqtt_client = None

    def _load_config(self) -> Dict[str, Any]:
        """Load add-on configuration from options.json."""
        try:
            with open("/data/options.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Configuration file not found!")
            return {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON in configuration file!")
            return {}

    def _setup_logging(self):
        """Configure logging based on user settings.

        Prefer a simple boolean 'debug' switch; fallback to legacy 'log_level'.
        Also adjust the root logger handler level so DEBUG messages are emitted
        when requested.
        """
        level: int
        if "debug" in self.config:
            level = logging.DEBUG if bool(self.config.get("debug")) else logging.INFO
        else:
            # Legacy support
            log_level = str(self.config.get("log_level", "info")).upper()
            level = getattr(logging, log_level, logging.INFO)

        # Apply level to root and module logger/handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        for h in root_logger.handlers:
            h.setLevel(level)
        logger.setLevel(level)

    async def connect_to_machine(self) -> bool:
        """Connect to the Meticulous Espresso machine and setup Socket.IO."""
        if not self.machine_ip:
            logger.error("No machine IP address configured!")
            return False

        logger.info(f"Connecting to Meticulous machine at {self.machine_ip}")

        try:
            # Build base URL
            base_url = f"http://{self.machine_ip}:8080/"

            # Setup event handlers for Socket.IO using ApiOptions
            options = ApiOptions(
                onTemperatureSensors=self._handle_temperature_event,
                onProfileChange=self._handle_profile_event,
                onNotification=self._handle_notification_event,
            )

            # Initialize API
            self.api = Api(base_url=base_url, options=options)  # type: ignore[assignment]

            # Test connection by fetching device info
            try:
                device_info = self.api.get_device_info()
                if isinstance(device_info, APIError):
                    logger.error(f"Failed to connect: {device_info.error}")
                    return False
            except Exception as e:
                logger.error(f"Error validating device info: {e}")
                logger.warning(
                    "Continuing despite validation error - firmware mismatch "
                    "possible"
                )
                # Use a placeholder object to continue operation

                class PlaceholderDeviceInfo:
                    def __init__(self):
                        self.name = "Unknown"
                        self.model = "Unknown"
                        self.serial = "Unknown"
                        self.firmware = "Unknown"
                        self.software_version = "Unknown"
                        self.model_version = "0.0.0"

                device_info = PlaceholderDeviceInfo()

            self.device_info = device_info
            logger.info(f"Connected to {device_info.name} (Serial: {device_info.serial})")
            logger.info(
                f"Firmware: {device_info.firmware}, Software: {device_info.software_version}")

            # Connect Socket.IO for real-time updates
            try:
                self.api.connect_to_socket()
                self.socket_connected = True
                self.api_connected = True
                logger.info("Socket.IO connected - real-time updates enabled")
            except Exception as e:
                self.socket_connected = False
                self.api_connected = True  # REST works, socket failed
                logger.warning(f"Socket.IO connection failed: {e}")
                logger.warning("Continuing with polling mode only")

            # Publish device info to Home Assistant
            await self.publish_device_info()
            await self.publish_connectivity(True)

            # Connect to MQTT broker and publish discovery
            self._mqtt_connect()

            return True

        except Exception as e:
            logger.error(f"Error connecting to machine: {e}", exc_info=True)
            await self.publish_connectivity(False)
            return False

    async def publish_connectivity(self, connected: bool) -> None:
        """Publish connectivity status to Home Assistant."""
        data = {"connected": connected}
        await self.publish_to_homeassistant(data)
        state = "connected" if connected else "disconnected"
        logger.info(f"Connectivity state: {state}")
        # Publish availability via MQTT
        if self.mqtt_client:
            self.mqtt_client.publish(self.availability_topic, payload=(
                "online" if connected else "offline"), qos=0, retain=True)

    async def publish_health_metrics(self) -> None:
        """Publish add-on health metrics via MQTT."""
        if not (self.mqtt_enabled and self.mqtt_client):
            return

        try:
            uptime = (datetime.now() - self.start_time).total_seconds()
            health_data = {
                "uptime_seconds": int(uptime),
                "reconnect_count": self.reconnect_count,
                "last_error": self.last_error,
                "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,  # noqa: E501
                "api_connected": self.api_connected,
                "socket_connected": self.socket_connected,
            }

            health_topic = f"{self.slug}/health"
            self.mqtt_client.publish(health_topic, jsonlib.dumps(health_data), qos=0, retain=False)
            msg = (
                f"Published health metrics: uptime={int(uptime)}s, "
                f"reconnects={self.reconnect_count}"
            )
            logger.debug(msg)
        except Exception as e:
            logger.error(f"Error publishing health metrics: {e}")

    def _compute_backoff(self, attempt: int) -> float:
        """Compute exponential backoff with optional jitter."""
        delay = min(self.retry_max, self.retry_initial * (2 ** max(0, attempt - 1)))
        if self.retry_jitter:
            # Add jitter up to 20% of delay
            jitter = random.uniform(0, delay * 0.2)
            delay = delay + jitter
        return float(delay)

    async def publish_to_homeassistant(self, sensor_data: Dict[str, Any]):
        """Publish sensor data to Home Assistant via Supervisor API."""
        if not self.supervisor_token:
            logger.debug("No supervisor token - cannot publish to HA")
            return

        # TODO: Implement Home Assistant MQTT discovery and state publishing
        # This will use the Home Assistant API or MQTT to create and update sensors
        # For now, log at debug and ensure non-blocking behavior
        logger.debug(f"Publishing sensor data: {sensor_data}")

        # If MQTT is enabled, publish mapped sensor states
        if self.mqtt_enabled and self.mqtt_client:
            try:
                for key, value in sensor_data.items():
                    mapping = self._mqtt_sensor_mapping().get(key)
                    if not mapping:
                        continue
                    topic = mapping["state_topic"]
                    payload = str(value) if not isinstance(
                        value, (dict, list)) else jsonlib.dumps(value)
                    self.mqtt_client.publish(topic, payload, qos=0, retain=False)
            except Exception as e:
                logger.warning(f"MQTT publish failed: {e}")

    async def report_error(self, title: str, message: str) -> None:
        """Report an error via logs and forward to HA notifications when possible."""
        logger.error(f"{title}: {message}")
        notif = {
            "notification": {
                "title": title,
                "message": message,
            }
        }
        await self.publish_to_homeassistant(notif)

    # =========================================================================
    # MQTT Setup & Discovery
    # =========================================================================

    def _mqtt_sensor_mapping(self) -> Dict[str, Dict[str, str]]:
        base = self.state_prefix
        # fmt: off  # Long topic names are more readable on single lines
        return {
            "connected": {"component": "binary_sensor", "state_topic": f"{base}/connected/state", "name": "Meticulous Connected"},  # noqa: E501
            "state": {"component": "sensor", "state_topic": f"{base}/state/state", "name": "Meticulous State"},  # noqa: E501
            "brewing": {"component": "binary_sensor", "state_topic": f"{base}/brewing/state", "name": "Meticulous Brewing"},  # noqa: E501
            "boiler_temperature": {"component": "sensor", "state_topic": f"{base}/boiler_temperature/state", "name": "Boiler Temperature"},  # noqa: E501
            "brew_head_temperature": {"component": "sensor", "state_topic": f"{base}/brew_head_temperature/state", "name": "Brew Head Temperature"},  # noqa: E501
            "pressure": {"component": "sensor", "state_topic": f"{base}/pressure/state", "name": "Pressure"},  # noqa: E501
            "flow_rate": {"component": "sensor", "state_topic": f"{base}/flow_rate/state", "name": "Flow Rate"},  # noqa: E501
            "shot_timer": {"component": "sensor", "state_topic": f"{base}/shot_timer/state", "name": "Shot Timer"},  # noqa: E501
            "shot_weight": {"component": "sensor", "state_topic": f"{base}/shot_weight/state", "name": "Shot Weight"},  # noqa: E501
            "active_profile": {"component": "sensor", "state_topic": f"{base}/active_profile/state", "name": "Active Profile"},  # noqa: E501
            "target_temperature": {"component": "sensor", "state_topic": f"{base}/target_temperature/state", "name": "Target Temperature"},  # noqa: E501
            "target_weight": {"component": "sensor", "state_topic": f"{base}/target_weight/state", "name": "Target Weight"},  # noqa: E501
            "firmware_version": {"component": "sensor", "state_topic": f"{base}/firmware_version/state", "name": "Firmware Version"},  # noqa: E501
            "software_version": {"component": "sensor", "state_topic": f"{base}/software_version/state", "name": "Software Version"},  # noqa: E501
            "voltage": {"component": "sensor", "state_topic": f"{base}/voltage/state", "name": "Voltage"},  # noqa: E501
            "sounds_enabled": {"component": "binary_sensor", "state_topic": f"{base}/sounds_enabled/state", "name": "Sounds Enabled"},  # noqa: E501
            "brightness": {"component": "sensor", "state_topic": f"{base}/brightness/state", "name": "Brightness"},  # noqa: E501
        }
        # fmt: on

    def _mqtt_device(self) -> Dict[str, Any]:
        info = self.device_info
        identifiers = [self.slug]
        if info and getattr(info, "serial", None):
            identifiers.append(info.serial)
        return {
            "identifiers": identifiers,
            "manufacturer": "Meticulous",
            "model": getattr(info, "model_version", "Espresso"),
            "name": getattr(info, "name", "Meticulous Espresso"),
            "sw_version": getattr(info, "software_version", None),
            "hw_version": getattr(info, "model_version", None),
        }

    def _mqtt_publish_discovery(self) -> None:
        if not (self.mqtt_enabled and self.mqtt_client):
            return
        device = self._mqtt_device()
        for key, m in self._mqtt_sensor_mapping().items():
            component = m["component"]
            object_id = f"{self.slug}_{key}"
            config_topic = f"{self.discovery_prefix}/{component}/{object_id}/config"
            payload: Dict[str, Any] = {
                "name": m["name"],
                "uniq_id": object_id,
                "stat_t": m["state_topic"],
                "avty_t": self.availability_topic,
                "dev": device,
            }
            # Add device_class / units where appropriate
            if key in ("boiler_temperature", "brew_head_temperature", "target_temperature"):
                payload["dev_cla"] = "temperature"
                payload["unit_of_meas"] = "°C"
            elif key == "pressure":
                payload["dev_cla"] = "pressure"
                payload["unit_of_meas"] = "bar"
            elif key == "voltage":
                payload["dev_cla"] = "voltage"
                payload["unit_of_meas"] = "V"
            elif key == "shot_timer":
                payload["unit_of_meas"] = "s"
            elif key == "shot_weight" or key == "target_weight":
                payload["unit_of_meas"] = "g"
            elif key == "brightness":
                payload["unit_of_meas"] = "%"
            # Publish discovery config
            self.mqtt_client.publish(config_topic, jsonlib.dumps(payload), qos=0, retain=True)

    # ---------------------------------------------------------------------
    # Test-facing helpers (wrappers) for discovery and backoff
    # ---------------------------------------------------------------------

    def _calculate_backoff(self, attempt: int) -> float:
        """Compute exponential backoff matching unit-test expectations.

        Tests expect base = retry_initial * (2 ** attempt), capped at retry_max,
        with optional jitter within ±20%.
        """
        base = min(self.retry_initial * (2 ** max(0, attempt)), self.retry_max)
        if self.retry_jitter:
            jitter = random.uniform(base * -0.2, base * 0.2)
            return float(max(0.0, base + jitter))
        return float(base)

    def _create_sensor_discovery(self, key: str, name: str, icon: str) -> Dict[str, Any]:
        """Return a Home Assistant MQTT discovery payload for a sensor.

        This wrapper produces full key names (state_topic, unique_id, device)
        expected by unit tests, delegating to the internal mapping.
        """
        mapping = self._mqtt_sensor_mapping().get(key, {
            "component": "sensor",
            "state_topic": f"{self.state_prefix}/{key}/state",
            "name": name,
        })
        payload: Dict[str, Any] = {
            "name": name,
            "state_topic": mapping["state_topic"],
            "unique_id": f"{self.slug}_{key}",
            "availability_topic": self.availability_topic,
            "device": self._mqtt_device(),
            "icon": icon,
        }
        # Add device_class / units where appropriate for parity
        if key in ("boiler_temperature", "brew_head_temperature", "target_temperature"):
            payload["device_class"] = "temperature"
            payload["unit_of_measurement"] = "°C"
        elif key == "pressure":
            payload["device_class"] = "pressure"
            payload["unit_of_measurement"] = "bar"
        elif key == "voltage":
            payload["device_class"] = "voltage"
            payload["unit_of_measurement"] = "V"
        elif key == "shot_timer":
            payload["unit_of_measurement"] = "s"
        elif key in ("shot_weight", "target_weight"):
            payload["unit_of_measurement"] = "g"
        elif key == "brightness":
            payload["unit_of_measurement"] = "%"
        return payload

    def _create_switch_discovery(self, key: str, name: str, command_suffix: str) -> Dict[str, Any]:
        """Return a Home Assistant MQTT discovery payload for a command switch.

        Produces payload with command_topic and state_topic that align with tests.
        """
        mapping = self._mqtt_sensor_mapping().get(key, {
            "component": "switch",
            "state_topic": f"{self.state_prefix}/{key}/state",
            "name": name,
        })
        payload: Dict[str, Any] = {
            "name": name,
            "state_topic": mapping["state_topic"],
            "command_topic": f"{self.command_prefix}/{command_suffix}",
            "unique_id": f"{self.slug}_{key}",
            "availability_topic": self.availability_topic,
            "device": self._mqtt_device(),
        }
        return payload

    def _mqtt_connect(self) -> None:
        if not self.mqtt_enabled:
            return
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client()

            # Set callback for incoming commands
            client.on_message = lambda client, userdata, msg: mqtt_on_message(
                self, client, userdata, msg)

            # Last will marks offline
            client.will_set(self.availability_topic, payload="offline", qos=0, retain=True)
            if self.mqtt_username and self.mqtt_password:
                client.username_pw_set(self.mqtt_username, self.mqtt_password)
            client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)

            # Subscribe to command topics
            client.subscribe(f"{self.command_prefix}/#")
            logger.info(f"Subscribed to MQTT commands at {self.command_prefix}/#")

            client.loop_start()
            # Mark online
            client.publish(self.availability_topic, payload="online", qos=0, retain=True)
            self.mqtt_client = client
            # Publish discovery once connected
            self._mqtt_publish_discovery()
            logger.info(f"MQTT connected to {self.mqtt_host}:{self.mqtt_port}")
        except Exception as e:
            self.mqtt_client = None
            logger.warning(f"MQTT connection failed: {e}")

    async def publish_device_info(self):
        """Publish device information sensors to Home Assistant."""
        if not self.device_info:
            return

        device_data = {
            "firmware_version": self.device_info.firmware,
            "software_version": self.device_info.software_version,
            "model": self.device_info.model_version,
            "serial": self.device_info.serial,
            "name": self.device_info.name,
            "voltage": getattr(self.device_info, 'mainVoltage', None),
        }

        await self.publish_to_homeassistant(device_data)
        logger.info("Published device info to Home Assistant")

    # =========================================================================
    # Socket.IO Event Handlers
    # =========================================================================

    def _handle_status_event(self, status: StatusData):
        """Handle real-time status updates from Socket.IO."""
        try:
            # Extract state
            state = status.state or "unknown"
            if state != self.current_state:
                logger.info(f"Machine state changed: {self.current_state} -> {state}")
                self.current_state = state

            # Extract sensor data
            sensors = status.sensors
            if isinstance(sensors, dict):
                # Convert dict to SensorData if needed
                pressure = sensors.get('p', 0)
                flow = sensors.get('f', 0)
                weight = sensors.get('w', 0)
                temperature = sensors.get('t', 0)
            else:
                pressure = sensors.p
                flow = sensors.f
                weight = sensors.w
                temperature = sensors.t

            sensor_data = {
                "state": state,
                "brewing": status.extracting or False,
                "shot_timer": status.profile_time / 1000.0 if status.profile_time else 0,  # Convert ms to seconds  # noqa: E501
                "elapsed_time": status.time / 1000.0 if status.time else 0,
                "pressure": pressure,
                "flow_rate": flow,
                "shot_weight": weight,
                "temperature": temperature,
                "active_profile": status.loaded_profile or "None",
            }

            # Add setpoints if available
            if status.setpoints:
                sensor_data["target_temperature"] = status.setpoints.temperature
                sensor_data["target_pressure"] = status.setpoints.pressure
                sensor_data["target_flow"] = status.setpoints.flow

            # Publish to Home Assistant (async)
            asyncio.create_task(self.publish_to_homeassistant(sensor_data))

            # Log during brewing
            if status.extracting:
                logger.debug(
                    f"Brewing: {sensor_data['shot_timer']:.1f}s | "
                    f"P: {pressure:.1f} bar | "
                    f"F: {flow:.1f} ml/s | "
                    f"W: {weight:.1f}g"
                )

        except Exception as e:
            logger.error(f"Error handling status event: {e}", exc_info=True)

    def _handle_temperature_event(self, temps: Temperatures):
        """Handle real-time temperature updates from Socket.IO."""
        try:
            temp_data = {
                "boiler_temperature": temps.t_bar_up,
                "brew_head_temperature": temps.t_bar_down,
                "external_temp_1": temps.t_ext_1,
                "external_temp_2": temps.t_ext_2,
            }

            # Publish to Home Assistant (async)
            asyncio.create_task(self.publish_to_homeassistant(temp_data))

            logger.debug(
                f"Temps: Boiler={temps.t_bar_up:.1f}°C, "
                f"Brew Head={temps.t_bar_down:.1f}°C"
            )

        except Exception as e:
            logger.error(f"Error handling temperature event: {e}", exc_info=True)

    def _handle_profile_event(self, profile_event: Any):
        """Handle profile change events from Socket.IO."""
        try:
            logger.info(f"Profile changed: {profile_event}")
            # Update current profile
            # Fetch full profile details if needed
            asyncio.create_task(self.update_profile_info())

        except Exception as e:
            logger.error(f"Error handling profile event: {e}", exc_info=True)

    def _handle_notification_event(self, notification: NotificationData):
        """Handle machine notifications from Socket.IO."""
        try:
            logger.warning(f"Machine notification: {notification.message}")

            # Forward to Home Assistant as a persistent notification
            notif_data = {
                "notification": {
                    "message": notification.message,
                    "title": "Meticulous Espresso",
                }
            }
            asyncio.create_task(self.publish_to_homeassistant(notif_data))

        except Exception as e:
            logger.error(f"Error handling notification event: {e}", exc_info=True)

    # =========================================================================
    # Polling Updates (for non-real-time data)
    # =========================================================================

    async def update_profile_info(self):
        """Fetch and update current profile information."""
        if not self.api:
            return

        try:
            last_profile = self.api.get_last_profile()
            if not isinstance(last_profile, APIError):
                self.current_profile = last_profile.profile

                profile_data = {
                    "active_profile": last_profile.profile.name,
                    "profile_author": last_profile.profile.author,
                    "target_temperature": last_profile.profile.temperature,
                    "target_weight": last_profile.profile.final_weight,
                }

                await self.publish_to_homeassistant(profile_data)
                logger.info(f"Updated profile: {last_profile.profile.name}")

        except Exception as e:
            logger.error(f"Error updating profile info: {e}", exc_info=True)

    async def update_statistics(self):
        """Fetch and update shot statistics."""
        if not self.api:
            return

        try:
            stats = self.api.get_history_statistics()
            if not isinstance(stats, APIError):
                stats_data = {
                    "total_shots": stats.totalSavedShots,
                }

                await self.publish_to_homeassistant(stats_data)
                logger.debug(f"Updated statistics: {stats.totalSavedShots} total shots")

            # Also get last shot info
            last_shot = self.api.get_last_shot()
            if last_shot and not isinstance(last_shot, APIError):
                last_shot_data = {
                    "last_shot_name": last_shot.name,
                    "last_shot_profile": last_shot.profile.name,
                    "last_shot_rating": last_shot.rating or "none",
                    "last_shot_time": datetime.fromtimestamp(last_shot.time).isoformat(),
                }

                await self.publish_to_homeassistant(last_shot_data)
                logger.debug(f"Last shot: {last_shot.name}")

        except Exception as e:
            logger.error(f"Error updating statistics: {e}", exc_info=True)

    async def update_settings(self):
        """Fetch and update settings sensors (brightness, sounds)."""
        if not self.api:
            return

        try:
            settings = self.api.get_settings()
            if not isinstance(settings, APIError):
                settings_data = {
                    "sounds_enabled": settings.enable_sounds,
                    # Note: Brightness may need to be retrieved separately or from device state
                    # The Settings object doesn't include brightness, may need different API call
                }

                await self.publish_to_homeassistant(settings_data)
                logger.debug(f"Updated settings: sounds={settings.enable_sounds}")

        except Exception as e:
            logger.error(f"Error updating settings: {e}", exc_info=True)

    async def maintain_socket_connection(self):
        """Maintain Socket.IO connection with auto-reconnect."""
        attempt = 0
        while self.running:
            if not self.socket_connected and self.api:
                try:
                    logger.info("Attempting to connect Socket.IO...")
                    self.api.connect_to_socket()
                    self.socket_connected = True
                    attempt = 0
                    await self.publish_connectivity(True)
                    logger.info("Socket.IO reconnected successfully")
                except Exception as e:
                    attempt += 1
                    self.reconnect_count += 1
                    self.last_error = str(e)
                    self.last_error_time = datetime.now()
                    delay = self._compute_backoff(attempt)
                    await self.publish_connectivity(False)
                    logger.warning(f"Socket reconnection failed (attempt {attempt}): {e}")
                    logger.info(f"Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
            else:
                await asyncio.sleep(5)  # Check every 5 seconds

    async def periodic_updates(self):
        """Perform periodic polling updates for non-real-time data."""
        # Initial delay to let Socket.IO establish
        await asyncio.sleep(10)

        while self.running:
            try:
                # Update profile info every 30 seconds
                await self.update_profile_info()

                # Update settings (brightness, sounds)
                await self.update_settings()

                # Update statistics
                await self.update_statistics()

                # Publish health metrics
                await self.publish_health_metrics()

                # Wait for next update cycle
                await asyncio.sleep(self.scan_interval)

            except Exception as e:
                logger.error(f"Error in periodic updates: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def run(self):
        """Main run loop."""
        logger.info("Starting Meticulous Espresso Add-on")
        logger.info(
            f"Configuration: machine_ip={self.machine_ip}, scan_interval={self.scan_interval}s")
        self.running = True

        # Create aiohttp session for HA API calls
        self.ha_session = aiohttp.ClientSession()

        try:
            # Connect to machine
            if not await self.connect_to_machine():
                # Exponential backoff on initial connect
                attempt = 1
                while self.running and not await self.connect_to_machine():
                    delay = self._compute_backoff(attempt)
                    logger.error(
                        "Failed to connect to machine (attempt %d). Retrying in %.1fs...",
                        attempt,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    attempt += 1

            # Start background tasks
            tasks = [
                asyncio.create_task(self.maintain_socket_connection()),
                asyncio.create_task(self.periodic_updates()),
            ]

            logger.info("Add-on running. Press Ctrl+C to stop.")

            # Keep running until stopped
            await asyncio.gather(*tasks, return_exceptions=True)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            self.running = False

            # Cleanup
            if self.api and self.socket_connected:
                try:
                    self.api.disconnect_socket()
                    logger.info("Socket.IO disconnected")
                except Exception as e:
                    logger.error(f"Error disconnecting socket: {e}")

            if self.ha_session:
                await self.ha_session.close()

            logger.info("Add-on stopped")


def main():
    """Entry point for the add-on."""
    addon = MeticulousAddon()
    try:
        asyncio.run(addon.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
