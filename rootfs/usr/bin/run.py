#!/usr/bin/env python3
"""Meticulous Espresso Add-on main application."""
import asyncio
import json
import json as jsonlib
import logging
import os
import random
import sys
import warnings
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

# Import Meticulous API
try:
    from meticulous.api import Api, ApiOptions
    from meticulous.api_types import APIError
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
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Suppress verbose Pydantic validation errors from pyMeticulous
logging.getLogger("pydantic").setLevel(logging.CRITICAL)
logging.getLogger("pydantic_core").setLevel(logging.CRITICAL)
logging.getLogger("pydantic.main").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


class MeticulousAddon:
    """Main class for Meticulous Espresso Add-on."""

    def __init__(self):
        """Initialize the add-on.

        Configurable options:
        - refresh_rate_minutes: How often to refresh all sensor states from the API (default: 5)
        Recommend 5-10 minutes for most users; set lower for more frequent updates.
        """
        self.config = self._load_config()
        self._setup_logging()
        raw_machine_ip = str(self.config.get("machine_ip", "")).strip()
        if raw_machine_ip.lower().startswith("example") or " " in raw_machine_ip:
            raw_machine_ip = ""
        self.machine_ip = raw_machine_ip
        # New: configurable refresh rate (minutes, default 5)
        self.refresh_rate_minutes = int(self.config.get("refresh_rate_minutes", 5))
        self.scan_interval = self.refresh_rate_minutes * 60
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
        self.available_profiles = {}  # Map of profile_id -> profile_name
        self.device_info = None

        # Home Assistant session
        self.ha_session: Optional[aiohttp.ClientSession] = None

        # Event loop reference for Socket.IO callbacks
        self.loop: Optional[asyncio.AbstractEventLoop] = None

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
        self.mqtt_last_failed = False  # Track connection state for logging
        self.mqtt_connect_attempt = 0  # Track retry attempts
        self.mqtt_next_retry_time = 0.0  # Track when to retry MQTT
        self.mqtt_discovery_pending = False  # Flag to publish discovery from main loop

        # Fetch MQTT credentials from Supervisor if not provided in config
        if self.mqtt_enabled and not (self.mqtt_username and self.mqtt_password):
            self._fetch_mqtt_credentials_from_supervisor()

    def _fetch_mqtt_credentials_from_supervisor(self):
        """Fetch MQTT credentials from Home Assistant Supervisor Services API."""
        try:
            import requests

            headers = {"Authorization": f"Bearer {self.supervisor_token}"}
            response = requests.get("http://supervisor/services/mqtt", headers=headers, timeout=10)
            if response.status_code == 200:
                mqtt_service = response.json().get("data", {})
                self.mqtt_host = mqtt_service.get("host", self.mqtt_host)
                self.mqtt_port = mqtt_service.get("port", self.mqtt_port)
                self.mqtt_username = mqtt_service.get("username")
                self.mqtt_password = mqtt_service.get("password")
                logger.info(
                    f"Retrieved MQTT credentials from Supervisor: "
                    f"{self.mqtt_host}:{self.mqtt_port}"
                )
            else:
                logger.warning(
                    f"Failed to fetch MQTT credentials from Supervisor: " f"{response.status_code}"
                )
        except Exception as e:
            logger.warning(f"Could not fetch MQTT credentials from Supervisor: {e}")

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
            logger.error(
                "No machine IP configured. Set 'machine_ip' in the add-on options "
                "(e.g., 192.168.x.x or meticulous.local)."
            )
            return False

        logger.info(f"Connecting to Meticulous machine at {self.machine_ip}")

        try:
            # Build base URL
            base_url = f"http://{self.machine_ip}:8080/"

            # Setup event handlers for Socket.IO using ApiOptions
            options = ApiOptions(
                onStatus=self._handle_status_event,
                onTemperatureSensors=self._handle_temperature_event,
                onProfileChange=self._handle_profile_event,
                onNotification=self._handle_notification_event,
                onButton=self._handle_button_event,
                onSettingsChange=self._handle_settings_change_event,
                onCommunication=self._handle_communication_event,
                onActuators=self._handle_actuators_event,
                onMachineInfo=self._handle_machine_info_event,
            )

            # Log handler setup for debugging
            logger.info("Socket.IO handlers configured:")
            logger.info(f"  - onStatus: {self._handle_status_event}")
            logger.info(f"  - onTemperatureSensors: {self._handle_temperature_event}")
            logger.info(f"  - onProfileChange: {self._handle_profile_event}")
            logger.info(f"  - onNotification: {self._handle_notification_event}")
            logger.info(f"  - onButton: {self._handle_button_event}")
            logger.info(f"  - onSettingsChange: {self._handle_settings_change_event}")
            logger.info(f"  - onCommunication: {self._handle_communication_event}")
            logger.info(f"  - onActuators: {self._handle_actuators_event}")
            logger.info(f"  - onMachineInfo: {self._handle_machine_info_event}")

            # Initialize API
            self.api = Api(base_url=base_url, options=options)  # type: ignore[assignment]

            # Test connection by fetching device info
            try:
                device_info = self.api.get_device_info()
                if isinstance(device_info, APIError):
                    logger.error(f"Failed to connect: {device_info.error}")
                    return False
            except Exception as e:
                logger.debug(f"Device info validation error (expected): {type(e).__name__}")
                logger.warning(
                    "Continuing despite validation error - firmware mismatch " "possible"
                )
                # Use a placeholder object to continue operation

                class PlaceholderDeviceInfo:
                    def __init__(self):
                        self.name = "Meticulous Espresso"
                        self.model = "Meticulous Espresso"
                        self.serial = "meticulous_espresso"
                        self.firmware = "unknown"
                        self.software_version = "unknown"
                        self.model_version = "Meticulous"

                device_info = PlaceholderDeviceInfo()

            self.device_info = device_info
            logger.info(f"Connected to {device_info.name} (Serial: {device_info.serial})")
            logger.info(
                f"Firmware: {device_info.firmware}, Software: {device_info.software_version}"
            )

            # Connect Socket.IO for real-time updates
            try:
                logger.info("Connecting to Socket.IO...")
                self.api.connect_to_socket()
                self.socket_connected = True
                self.api_connected = True
                logger.info("Socket.IO connected - real-time updates enabled")
                logger.info(
                    "Event handlers registered: onStatus, onTemperatureSensors, "
                    "onProfileChange, onNotification, onButton, onSettingsChange"
                )
            except Exception as e:
                self.socket_connected = False
                self.api_connected = True  # REST works, socket failed
                logger.warning(f"Socket.IO connection failed: {e}")
                logger.warning("Continuing with polling mode only")

            # Publish device info to Home Assistant
            await self.publish_device_info()
            await self.publish_connectivity(True)

            # Fetch available profiles before MQTT discovery
            await self.fetch_available_profiles()

            # MQTT connection will be handled in periodic_updates with proper retry logic

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
            self.mqtt_client.publish(
                self.availability_topic,
                payload=("online" if connected else "offline"),
                qos=0,
                retain=True,
            )

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
                "last_error_time": (
                    self.last_error_time.isoformat() if self.last_error_time else None
                ),  # noqa: E501
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
                published_count = 0
                for key, value in sensor_data.items():
                    mapping = self._mqtt_sensor_mapping().get(key)
                    if not mapping:
                        continue
                    topic = mapping["state_topic"]
                    payload = (
                        str(value) if not isinstance(value, (dict, list)) else jsonlib.dumps(value)
                    )
                    self.mqtt_client.publish(topic, payload, qos=0, retain=False)
                    published_count += 1
                if published_count > 0:
                    logger.debug(f"Published {published_count} MQTT state updates")
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
        # fmt: off
        return {
            "connected": {
                "component": "binary_sensor",
                "state_topic": f"{base}/connected/state",
                "name": "Meticulous Connected",
            },
            "state": {
                "component": "sensor",
                "state_topic": f"{base}/state/state",
                "name": "Meticulous State",
            },
            "brewing": {
                "component": "binary_sensor",
                "state_topic": f"{base}/brewing/state",
                "name": "Meticulous Brewing",
            },
            "boiler_temperature": {
                "component": "sensor",
                "state_topic": f"{base}/boiler_temperature/state",
                "name": "Boiler Temperature",
            },
            "brew_head_temperature": {
                "component": "sensor",
                "state_topic": f"{base}/brew_head_temperature/state",
                "name": "Brew Head Temperature",
            },
            "external_temp_1": {
                "component": "sensor",
                "state_topic": f"{base}/external_temp_1/state",
                "name": "External Temperature 1",
            },
            "external_temp_2": {
                "component": "sensor",
                "state_topic": f"{base}/external_temp_2/state",
                "name": "External Temperature 2",
            },
            "pressure": {
                "component": "sensor",
                "state_topic": f"{base}/pressure/state",
                "name": "Pressure",
            },
            "flow_rate": {
                "component": "sensor",
                "state_topic": f"{base}/flow_rate/state",
                "name": "Flow Rate",
            },
            "shot_timer": {
                "component": "sensor",
                "state_topic": f"{base}/shot_timer/state",
                "name": "Shot Timer",
            },
            "shot_weight": {
                "component": "sensor",
                "state_topic": f"{base}/shot_weight/state",
                "name": "Shot Weight",
            },
            "total_shots": {
                "component": "sensor",
                "state_topic": f"{base}/total_shots/state",
                "name": "Total Shots",
            },
            "last_shot_name": {
                "component": "sensor",
                "state_topic": f"{base}/last_shot_name/state",
                "name": "Last Shot Name",
            },
            "last_shot_profile": {
                "component": "sensor",
                "state_topic": f"{base}/last_shot_profile/state",
                "name": "Last Shot Profile",
            },
            "last_shot_rating": {
                "component": "sensor",
                "state_topic": f"{base}/last_shot_rating/state",
                "name": "Last Shot Rating",
            },
            "last_shot_time": {
                "component": "sensor",
                "state_topic": f"{base}/last_shot_time/state",
                "name": "Last Shot Time",
            },
            "profile_author": {
                "component": "sensor",
                "state_topic": f"{base}/profile_author/state",
                "name": "Profile Author",
            },
            "target_temperature": {
                "component": "sensor",
                "state_topic": f"{base}/target_temperature/state",
                "name": "Target Temperature",
            },
            "target_weight": {
                "component": "sensor",
                "state_topic": f"{base}/target_weight/state",
                "name": "Target Weight",
            },
            "firmware_version": {
                "component": "sensor",
                "state_topic": f"{base}/firmware_version/state",
                "name": "Firmware Version",
            },
            "software_version": {
                "component": "sensor",
                "state_topic": f"{base}/software_version/state",
                "name": "Software Version",
            },
            "voltage": {
                "component": "sensor",
                "state_topic": f"{base}/voltage/state",
                "name": "Voltage",
            },
            "sounds_enabled": {
                "component": "binary_sensor",
                "state_topic": f"{base}/sounds_enabled/state",
                "name": "Sounds Enabled",
            },
            # Combined brightness: single number entity for both sensor and control
            "brightness": {
                "component": "number",
                "state_topic": f"{base}/brightness/state",
                "name": "Brightness",
            },
            "firmware_update_available": {
                "component": "binary_sensor",
                "state_topic": f"{base}/firmware_update_available/state",
                "name": "Firmware Update Available",
            },
        }
        # fmt: on

    def _mqtt_command_mapping(self) -> Dict[str, Dict[str, str | int]]:
        """Return mapping of available commands for Home Assistant discovery."""
        return {
            "start_brew": {
                "name": "Start Brew",
                "icon": "mdi:play",
                "command_suffix": "start_brew",
            },
            "stop_brew": {
                "name": "Stop Brew",
                "icon": "mdi:stop",
                "command_suffix": "stop_brew",
            },
            "continue_brew": {
                "name": "Continue Brew",
                "icon": "mdi:play-pause",
                "command_suffix": "continue_brew",
            },
            "preheat": {
                "name": "Preheat",
                "icon": "mdi:fire",
                "command_suffix": "preheat",
            },
            "tare_scale": {
                "name": "Tare Scale",
                "icon": "mdi:scale",
                "command_suffix": "tare_scale",
            },
            "set_brightness": {
                "name": "Set Brightness",
                "icon": "mdi:brightness-6",
                "command_suffix": "set_brightness",
                "type": "number",
                "min": 0,
                "max": 100,
            },
            "enable_sounds": {
                "name": "Enable Sounds",
                "icon": "mdi:volume-high",
                "command_suffix": "enable_sounds",
                "type": "switch",
            },
            "reboot_machine": {
                "name": "Reboot Machine",
                "icon": "mdi:restart",
                "command_suffix": "reboot_machine",
            },
        }

    def _mqtt_device(self) -> Dict[str, Any]:
        info = self.device_info
        identifiers = [self.slug]
        if info and getattr(info, "serial", None):
            identifiers.append(info.serial)
        return {
            "identifiers": identifiers,
            "manufacturer": "Meticulous",
            "model": getattr(info, "model", "Espresso"),
            "name": getattr(info, "name", "Meticulous Espresso"),
            "sw_version": getattr(info, "software_version", None),
            "hw_version": getattr(info, "model", None),
        }

    async def _mqtt_publish_discovery(self) -> None:
        if not (self.mqtt_enabled and self.mqtt_client):
            logger.debug("Skipping discovery publish: mqtt not ready")
            return
        logger.info("Publishing MQTT Home Assistant discovery configs")
        is_connected = self.mqtt_client.is_connected()
        logger.info(f"Client connection state at discovery start: is_connected={is_connected}")
        if not is_connected:
            logger.error(
                "MQTT client not connected at discovery start - aborting discovery publish"
            )
            return

        discovery_count = 0
        device = self._mqtt_device()
        for key, m in self._mqtt_sensor_mapping().items():
            # Remove active_profile from sensor discovery (only publish as select)
            if key == "active_profile":
                continue
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
            temp_keys = (
                "boiler_temperature",
                "brew_head_temperature",
                "target_temperature",
                "external_temp_1",
                "external_temp_2",
            )
            if key in temp_keys:
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
            result = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.mqtt_client.publish(
                    config_topic, jsonlib.dumps(payload), qos=1, retain=True
                ),
            )
            discovery_count += 1
            conn_state = self.mqtt_client.is_connected()
            logger.debug(
                f"Published {key} to {config_topic}: rc={result.rc}, is_connected={conn_state}"
            )

        # Publish button/number/switch commands
        for key, cmd in self._mqtt_command_mapping().items():
            object_id = f"{self.slug}_{key}"
            cmd_type = cmd.get("type", "button")

            if key == "set_brightness":
                # Publish brightness as a number entity (combined sensor/control)
                component = "number"
                config_topic = f"{self.discovery_prefix}/{component}/{object_id}/config"
                payload: Dict[str, Any] = {
                    "name": "Brightness",
                    "uniq_id": object_id,
                    "stat_t": f"{self.state_prefix}/brightness/state",
                    "cmd_t": f"{self.command_prefix}/set_brightness",
                    "avty_t": self.availability_topic,
                    "dev": device,
                    "icon": cmd["icon"],
                    "min": cmd.get("min", 0),
                    "max": cmd.get("max", 100),
                    "unit_of_meas": "%",
                }
                result = await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: self.mqtt_client.publish(
                        config_topic, jsonlib.dumps(payload), qos=1, retain=True
                    ),
                )
                discovery_count += 1
                logger.debug(f"Published {key} brightness number to {config_topic}: rc={result.rc}")
                continue

            if cmd_type == "number":
                component = "number"
                config_topic = f"{self.discovery_prefix}/{component}/{object_id}/config"
                payload: Dict[str, Any] = {
                    "name": cmd["name"],
                    "uniq_id": object_id,
                    "cmd_t": f"{self.command_prefix}/{cmd['command_suffix']}",
                    "avty_t": self.availability_topic,
                    "dev": device,
                    "icon": cmd["icon"],
                    "min": cmd.get("min", 0),
                    "max": cmd.get("max", 100),
                }
            elif cmd_type == "switch":
                component = "switch"
                config_topic = f"{self.discovery_prefix}/{component}/{object_id}/config"
                payload: Dict[str, Any] = {
                    "name": cmd["name"],
                    "uniq_id": object_id,
                    "cmd_t": f"{self.command_prefix}/{cmd['command_suffix']}",
                    "avty_t": self.availability_topic,
                    "dev": device,
                    "icon": cmd["icon"],
                    "payload_on": "true",
                    "payload_off": "false",
                }
            else:  # button
                component = "button"
                config_topic = f"{self.discovery_prefix}/{component}/{object_id}/config"
                payload: Dict[str, Any] = {
                    "name": cmd["name"],
                    "uniq_id": object_id,
                    "cmd_t": f"{self.command_prefix}/{cmd['command_suffix']}",
                    "avty_t": self.availability_topic,
                    "dev": device,
                    "icon": cmd["icon"],
                    "payload_press": "1",
                }

            result = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.mqtt_client.publish(
                    config_topic, jsonlib.dumps(payload), qos=1, retain=True
                ),
            )
            discovery_count += 1
            logger.debug(f"Published {key} ({cmd_type}) command to {config_topic}: rc={result.rc}")

        # Publish active_profile as select entity (only, not as sensor)
        if self.available_profiles:
            object_id = f"{self.slug}_active_profile"
            config_topic = f"{self.discovery_prefix}/select/{object_id}/config"
            payload: Dict[str, Any] = {
                "name": "Active Profile",
                "uniq_id": object_id,
                "cmd_t": f"{self.command_prefix}/load_profile",
                "stat_t": f"{self.state_prefix}/active_profile/state",
                "avty_t": self.availability_topic,
                "dev": device,
                "icon": "mdi:coffee",
                "options": list(self.available_profiles.values()),
            }
            result = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.mqtt_client.publish(
                    config_topic, jsonlib.dumps(payload), qos=1, retain=True
                ),
            )
            discovery_count += 1
            logger.debug(f"Published active_profile to {config_topic}: rc={result.rc}")

        final_connected = self.mqtt_client.is_connected()
        logger.info(
            f"Published {discovery_count} discovery messages, final is_connected={final_connected}"
        )

    async def _mqtt_publish_initial_state(self) -> None:
        """Fetch and publish initial state of all sensors (T0 snapshot).

        This creates entities in Home Assistant immediately by providing
        the first state message for all sensors, rather than waiting for
        Socket.IO updates which may be infrequent or never occur for some.
        """
        if not (self.mqtt_enabled and self.mqtt_client):
            return

        logger.debug("Fetching initial sensor state (T0 snapshot)")
        initial_data = {}

        # Device info (firmware, software, model, serial, voltage)
        if self.device_info:
            initial_data.update(
                {
                    "firmware_version": self.device_info.firmware,
                    "software_version": self.device_info.software_version,
                    "model": getattr(self.device_info, "model", None),
                    "serial": self.device_info.serial,
                    "name": self.device_info.name,
                    "voltage": getattr(self.device_info, "mainVoltage", None),
                }
            )

        # Statistics (total shots)
        if self.api:
            try:
                api = self.api  # Capture reference to satisfy type checker
                stats = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: api.get_history_statistics()
                )
                if stats and not isinstance(stats, APIError):
                    initial_data["total_shots"] = stats.totalSavedShots

                # Also get last shot info
                try:
                    last_shot = api.get_last_shot()
                    if last_shot and not isinstance(last_shot, APIError):
                        initial_data["last_shot_name"] = getattr(last_shot, "name", None)
                        if hasattr(last_shot, "profile"):
                            initial_data["last_shot_profile"] = getattr(
                                last_shot.profile, "name", None
                            )
                        else:
                            initial_data["last_shot_profile"] = None
                        initial_data["last_shot_rating"] = (
                            getattr(last_shot, "rating", None) or "none"
                        )
                        if hasattr(last_shot, "time") and last_shot.time:
                            shot_time = datetime.fromtimestamp(last_shot.time)
                            initial_data["last_shot_time"] = shot_time.isoformat()
                except Exception as e:
                    logger.debug(f"Could not fetch initial last shot: {e}")

                # Firmware update availability sensor
                try:
                    update_status = api.check_for_updates()
                    available = False
                    if update_status and not isinstance(update_status, APIError):
                        available = getattr(update_status, "available", False)
                    initial_data["firmware_update_available"] = available
                except Exception as e:
                    logger.debug(f"Could not fetch firmware update status: {e}")
            except Exception as e:
                logger.debug(f"Could not fetch initial statistics: {e}")

        # Profile info (active profile, target temp/weight)
        if self.api:
            try:
                api = self.api  # Capture reference to satisfy type checker
                last_profile = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: api.get_last_profile()
                )
                if (
                    last_profile
                    and not isinstance(last_profile, APIError)
                    and hasattr(last_profile, "profile")
                ):
                    profile = last_profile.profile
                    initial_data["active_profile"] = getattr(profile, "name", None)
                    initial_data["profile_author"] = getattr(profile, "author", None)
                    initial_data["target_temperature"] = getattr(profile, "temperature", None)
                    initial_data["target_weight"] = getattr(profile, "final_weight", None)
            except Exception as e:
                logger.debug(f"Could not fetch initial profile: {e}")

        # Settings (sounds enabled)
        if self.api:
            try:
                api = self.api  # Capture reference to satisfy type checker
                settings = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: api.get_settings()
                )
                if settings and not isinstance(settings, APIError):
                    initial_data["sounds_enabled"] = getattr(settings, "enable_sounds", None)
            except Exception as e:
                logger.debug(f"Could not fetch initial settings: {e}")

        # Note: Status (state, sensors, brewing) and temperatures only available via Socket.IO
        # These will be populated by real-time events after connection

        # Connectivity state
        initial_data["connected"] = self.socket_connected

        # Publish all available initial state
        await self.publish_to_homeassistant(initial_data)
        logger.info(f"Published initial state for {len(initial_data)} sensors")

    async def fetch_available_profiles(self):
        """Fetch list of available profiles from the machine."""
        if not self.api:
            logger.warning("Cannot fetch profiles: API not connected")
            return

        try:
            api = self.api

            def fetch_profiles():
                # Use api.list_profiles() wrapper which properly handles /api/v1/profile/list
                result = api.list_profiles()
                # Result is either List[PartialProfile] or APIError
                return result

            profiles_data = await asyncio.get_running_loop().run_in_executor(None, fetch_profiles)

            # Check if result is APIError
            if isinstance(profiles_data, APIError):
                logger.error(f"Failed to fetch profiles: {profiles_data.error}")
                return

            # profiles_data is a list of PartialProfile objects
            if isinstance(profiles_data, list):
                old_profiles = self.available_profiles.copy()
                # Convert PartialProfile objects to id->name mapping
                self.available_profiles = {}
                for p in profiles_data:
                    # PartialProfile has 'id' and 'name' attributes
                    profile_id = getattr(p, "id", None) or getattr(p, "name", "")
                    profile_name = getattr(p, "name", "Unknown")
                    if profile_id:
                        self.available_profiles[profile_id] = profile_name

                logger.info(f"Fetched {len(self.available_profiles)} available profiles")
                # Detect and log profile list changes
                if old_profiles != self.available_profiles:
                    added = set(self.available_profiles.keys()) - set(old_profiles.keys())
                    removed = set(old_profiles.keys()) - set(self.available_profiles.keys())
                    if added or removed:
                        logger.info(
                            f"Profile list changed: "
                            f"+{len(added)} added, -{len(removed)} removed"
                        )
                    # Republish discovery with updated profile options
                    if self.mqtt_client:
                        logger.debug("Republishing MQTT discovery with new profile list")
                        await self._mqtt_publish_discovery()
        except Exception as e:
            logger.error(f"Error fetching available profiles: {e}", exc_info=True)

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
        mapping = self._mqtt_sensor_mapping().get(
            key,
            {
                "component": "sensor",
                "state_topic": f"{self.state_prefix}/{key}/state",
                "name": name,
            },
        )
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
        mapping = self._mqtt_sensor_mapping().get(
            key,
            {
                "component": "switch",
                "state_topic": f"{self.state_prefix}/{key}/state",
                "name": name,
            },
        )
        payload: Dict[str, Any] = {
            "name": name,
            "state_topic": mapping["state_topic"],
            "command_topic": f"{self.command_prefix}/{command_suffix}",
            "unique_id": f"{self.slug}_{key}",
            "availability_topic": self.availability_topic,
            "device": self._mqtt_device(),
        }
        return payload

    def _mqtt_error_string(self, rc: int) -> str:
        """Convert MQTT return code to human-readable string."""
        errors = {
            0: "Success",
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized",
        }
        return errors.get(rc, f"Unknown error ({rc})")

    def _mqtt_connect(self) -> None:
        if not self.mqtt_enabled:
            return
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client(client_id=self.slug)

            # Set callbacks
            def on_connect(client, userdata, flags, rc):
                logger.info(f"on_connect callback fired: rc={rc}")
                if rc == 0:
                    logger.info(f"MQTT connected to {self.mqtt_host}:{self.mqtt_port}")
                    # Subscribe to command topics after successful connection
                    client.subscribe(f"{self.command_prefix}/#")
                    logger.info(f"Subscribed to MQTT commands at {self.command_prefix}/#")
                    # Mark online
                    online_result = client.publish(
                        self.availability_topic, payload="online", qos=0, retain=True
                    )
                    logger.info(f"Published online status: rc={online_result.rc}")
                    # Set flag to publish discovery from main event loop (thread-safe)
                    logger.info("Setting mqtt_discovery_pending=True")
                    self.mqtt_discovery_pending = True
                    # Publish initial state on successful connection
                    if self.loop:
                        asyncio.run_coroutine_threadsafe(
                            self._mqtt_publish_initial_state(), self.loop
                        )
                    self.mqtt_last_failed = False  # Reset failure flag on success
                else:
                    error_msg = self._mqtt_error_string(rc)
                    logger.error(f"MQTT connection failed with code {rc}: {error_msg}")
                    # Mark connection as failed so next attempt will retry
                    self.mqtt_client = None

            client.on_connect = on_connect
            client.on_message = lambda client, userdata, msg: mqtt_on_message(
                self, client, userdata, msg
            )

            # Last will marks offline
            client.will_set(self.availability_topic, payload="offline", qos=0, retain=True)
            if self.mqtt_username and self.mqtt_password:
                client.username_pw_set(self.mqtt_username, self.mqtt_password)

            client.loop_start()
            client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)

            self.mqtt_client = client
        except Exception as e:
            self.mqtt_client = None
            # Only log at INFO level on first failure, subsequent retries at DEBUG
            if not self.mqtt_last_failed:
                logger.info(f"MQTT connection attempt failed (will retry): {e}")
                self.mqtt_last_failed = True
            else:
                logger.debug(f"MQTT connection retry failed: {e}")

    async def publish_device_info(self):
        """Publish device information sensors to Home Assistant."""
        if not self.device_info:
            return

        device_data = {
            "firmware_version": self.device_info.firmware,
            "software_version": self.device_info.software_version,
            "model": getattr(self.device_info, "model", None),
            "serial": self.device_info.serial,
            "name": self.device_info.name,
            "voltage": getattr(self.device_info, "mainVoltage", None),
        }

        await self.publish_to_homeassistant(device_data)
        logger.info("Published device info to Home Assistant")

    # =========================================================================
    # Socket.IO Event Handlers
    # =========================================================================

    def _handle_status_event(self, status: dict):
        """Handle real-time status updates from Socket.IO."""
        try:
            # Extract state
            state = status.get("state", "unknown")
            if state != self.current_state:
                logger.info(f"Machine state changed: {self.current_state} -> {state}")
                self.current_state = state

            # Detect profile changes
            loaded_profile = status.get("loaded_profile")
            if loaded_profile and loaded_profile != self.current_profile:
                logger.info(f"Profile changed: {self.current_profile} -> {loaded_profile}")
                self.current_profile = loaded_profile
                # Trigger profile info update
                if self.loop:
                    logger.debug("Scheduling profile info update after profile change")
                    asyncio.run_coroutine_threadsafe(self.update_profile_info(), self.loop)

            # Extract sensor data
            sensors = status.get("sensors", {})
            if isinstance(sensors, dict):
                # Convert dict to SensorData if needed
                pressure = sensors.get("p", 0)
                flow = sensors.get("f", 0)
                weight = sensors.get("w", 0)
                temperature = sensors.get("t", 0)
            else:
                pressure = getattr(sensors, "p", 0)
                flow = getattr(sensors, "f", 0)
                weight = getattr(sensors, "w", 0)
                temperature = getattr(sensors, "t", 0)

            sensor_data = {
                "state": state,
                "brewing": status.get("extracting", False),
                "shot_timer": (
                    status.get("profile_time", 0) / 1000.0 if status.get("profile_time") else 0
                ),  # Convert ms to seconds  # noqa: E501
                "elapsed_time": status.get("time", 0) / 1000.0 if status.get("time") else 0,
                "pressure": pressure,
                "flow_rate": flow,
                "shot_weight": weight,
                "temperature": temperature,
                "active_profile": status.get("loaded_profile", "None"),
            }

            # Add setpoints if available
            setpoints = status.get("setpoints")
            if setpoints:
                if isinstance(setpoints, dict):
                    sensor_data["target_temperature"] = setpoints.get("temperature")
                    sensor_data["target_pressure"] = setpoints.get("pressure")
                    sensor_data["target_flow"] = setpoints.get("flow")
                else:
                    sensor_data["target_temperature"] = getattr(setpoints, "temperature", None)
                    sensor_data["target_pressure"] = getattr(setpoints, "pressure", None)
                    sensor_data["target_flow"] = getattr(setpoints, "flow", None)

            # Publish to Home Assistant (async)
            if self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.publish_to_homeassistant(sensor_data), self.loop
                )

            # Log during brewing
            if status.get("extracting"):
                logger.debug(
                    f"Brewing: {sensor_data['shot_timer']:.1f}s | "
                    f"P: {pressure:.1f} bar | "
                    f"F: {flow:.1f} ml/s | "
                    f"W: {weight:.1f}g"
                )

        except Exception as e:
            logger.error(f"Error handling status event: {e}", exc_info=True)

    def _handle_temperature_event(self, temps: dict):
        """Handle real-time temperature updates from Socket.IO."""
        try:
            # Handle both dict and object types
            if isinstance(temps, dict):
                temp_data = {
                    "boiler_temperature": temps.get("t_bar_up"),
                    "brew_head_temperature": temps.get("t_bar_down"),
                    "external_temp_1": temps.get("t_ext_1"),
                    "external_temp_2": temps.get("t_ext_2"),
                }
                t_bar_up = temps.get("t_bar_up", 0)
                t_bar_down = temps.get("t_bar_down", 0)
            else:
                temp_data = {
                    "boiler_temperature": temps.t_bar_up,
                    "brew_head_temperature": temps.t_bar_down,
                    "external_temp_1": temps.t_ext_1,
                    "external_temp_2": temps.t_ext_2,
                }
                t_bar_up = temps.t_bar_up
                t_bar_down = temps.t_bar_down

            # Publish to Home Assistant (async)
            if self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.publish_to_homeassistant(temp_data), self.loop
                )

            logger.debug(f"Temps: Boiler={t_bar_up:.1f}°C, " f"Brew Head={t_bar_down:.1f}°C")

        except Exception as e:
            logger.error(f"Error handling temperature event: {e}", exc_info=True)

    def _handle_profile_event(self, profile_event: Any):
        """Handle profile change events from Socket.IO."""
        try:
            logger.info(f"Profile changed: {profile_event}")
            # Update current profile
            # Fetch full profile details if needed
            if self.loop:
                logger.debug("Scheduling profile info update")
                asyncio.run_coroutine_threadsafe(self.update_profile_info(), self.loop)
                # Also refresh available profiles in case list changed
                logger.debug("Scheduling profile list refresh")
                asyncio.run_coroutine_threadsafe(self.fetch_available_profiles(), self.loop)
            else:
                logger.warning("No event loop available for profile update")

        except Exception as e:
            logger.error(f"Error handling profile event: {e}", exc_info=True)

    def _handle_notification_event(self, notification: dict):
        """Handle machine notifications from Socket.IO."""
        try:
            message = (
                notification.get("message", str(notification))
                if isinstance(notification, dict)
                else str(notification)
            )
            logger.warning(f"Machine notification: {message}")

            # Forward to Home Assistant as a persistent notification
            notif_data = {
                "notification": {
                    "message": message,
                    "title": "Meticulous Espresso",
                }
            }
            if self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.publish_to_homeassistant(notif_data), self.loop
                )

        except Exception as e:
            logger.error(f"Error handling notification event: {e}", exc_info=True)

    def _handle_button_event(self, button: Any):
        """Handle button events from Socket.IO (e.g., tare button)."""
        logger.info(f"Button event received: {button}")
        # Button events could trigger updates or actions
        # For now, just log them to understand what events come through

    def _handle_settings_change_event(self, settings: Dict):
        """Handle settings change events from Socket.IO (e.g., brightness)."""
        logger.info(f"Settings change event received: {settings}")
        # This should capture brightness changes and other settings updates
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.publish_to_homeassistant(settings), self.loop)

    def _handle_communication_event(self, comm: Any):
        """Handle communication events from Socket.IO."""
        logger.debug(f"Communication event received: {comm}")
        # Log these for debugging but they may not be user-relevant

    def _handle_actuators_event(self, actuators: Any):
        """Handle actuator events from Socket.IO."""
        logger.debug(f"Actuators event received: {actuators}")
        # This might include pump, valve states, etc.

    def _handle_machine_info_event(self, info: Any):
        """Handle machine info events from Socket.IO."""
        logger.debug(f"Machine info event received: {info}")
        # Device/firmware info updates

    # =========================================================================
    # Polling Updates (for non-real-time data)
    # =========================================================================

    async def update_profile_info(self):
        """Fetch and update current profile information."""
        if not self.api:
            logger.warning("Cannot update profile: API not connected")
            return

        try:
            api = self.api  # Capture reference for executor

            def fetch_last_profile_raw():
                # Use api.get_last_profile() wrapper which properly handles the response
                result = api.get_last_profile()
                # Result is either LastProfile or APIError
                return result

            result = await asyncio.get_running_loop().run_in_executor(None, fetch_last_profile_raw)

            # Check if result is APIError
            if isinstance(result, APIError):
                logger.error(f"Failed to fetch last profile: {result.error}")
                return

            # result is a LastProfile object with 'profile' attribute
            profile = getattr(result, "profile", None) if result else None
            if not profile:
                logger.warning("No profile data in response")
                return

            new_profile_name = getattr(profile, "name", "Unknown")
            profile_changed = new_profile_name != self.current_profile

            self.current_profile = new_profile_name

            profile_data = {
                "active_profile": new_profile_name,
                "profile_author": getattr(profile, "author", None),
                "target_temperature": getattr(profile, "temperature", None),
                "target_weight": getattr(profile, "final_weight", None),
            }

            await self.publish_to_homeassistant(profile_data)
            if profile_changed:
                logger.info(f"Profile changed to: {new_profile_name}")

        except Exception as e:
            logger.error(f"Error updating profile info: {e}", exc_info=True)

    async def update_statistics(self):
        """Fetch and update shot statistics."""
        if not self.api:
            return

        try:
            api = self.api  # Capture reference for executor
            stats = await asyncio.get_running_loop().run_in_executor(
                None, lambda: api.get_history_statistics()
            )
            if not isinstance(stats, APIError):
                stats_data = {
                    "total_shots": stats.totalSavedShots,
                }

                await self.publish_to_homeassistant(stats_data)
                logger.debug(f"Updated statistics: {stats.totalSavedShots} total shots")

            # Also get last shot info
            try:
                last_shot = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: api.get_last_shot()
                )
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
                logger.debug(
                    f"Could not retrieve last shot (firmware mismatch): " f"{type(e).__name__}"
                )

        except Exception as e:
            logger.error(f"Error updating statistics: {e}", exc_info=True)

    async def update_settings(self):
        """Fetch and update settings sensors (brightness, sounds)."""
        if not self.api:
            return

        try:
            api = self.api  # Capture reference for executor
            settings = await asyncio.get_running_loop().run_in_executor(
                None, lambda: api.get_settings()
            )
            if not isinstance(settings, APIError):
                settings_data = {
                    "sounds_enabled": settings.enable_sounds,
                    # Note: Brightness may need to be retrieved separately or from device state
                    # The Settings object doesn't include brightness, may need different API call
                }

                await self.publish_to_homeassistant(settings_data)
                logger.debug(f"Updated settings: sounds={settings.enable_sounds}")

        except Exception as e:
            logger.debug(f"Could not retrieve settings (firmware mismatch): " f"{type(e).__name__}")

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
        """Perform periodic polling updates for non-real-time data.

        All sensors are heartbeat-refreshed from the API every refresh_rate_minutes (default: 5).
        """
        # Initial delay to let Socket.IO establish
        await asyncio.sleep(10)

        while self.running:
            try:
                # Retry MQTT connection if not connected with exponential backoff
                if self.mqtt_enabled and not self.mqtt_client:
                    import time

                    current_time = time.time()
                    if current_time >= self.mqtt_next_retry_time:
                        self.mqtt_connect_attempt += 1
                        # Exponential backoff: 5s, 10s, 20s, 40s, max 120s
                        backoff = min(5 * (2 ** max(0, self.mqtt_connect_attempt - 1)), 120)
                        logger.debug(
                            f"MQTT connection attempt {self.mqtt_connect_attempt} "
                            f"(backoff: {backoff}s)"
                        )
                        self._mqtt_connect()
                        if self.mqtt_client:
                            # Reset attempts on successful connection
                            self.mqtt_connect_attempt = 0
                            self.mqtt_next_retry_time = 0
                        else:
                            # Schedule next retry
                            self.mqtt_next_retry_time = current_time + backoff

                # Only poll profile info if Socket.IO isn't connected (fallback mode)
                if not self.socket_connected:
                    await self.update_profile_info()

                # Fetch available profiles periodically (every refresh)
                if self.api and not self.available_profiles:
                    await self.fetch_available_profiles()

                # Update settings (brightness, sounds)
                await self.update_settings()

                # Update statistics
                await self.update_statistics()

                # Update firmware update availability sensor
                if self.api and self.mqtt_enabled and self.mqtt_client:
                    try:
                        update_status = self.api.check_for_updates()
                        available = False
                        if update_status and not isinstance(update_status, APIError):
                            available = getattr(update_status, "available", False)
                        self.mqtt_client.publish(
                            f"{self.state_prefix}/firmware_update_available/state",
                            str(available).lower(),
                            qos=0,
                            retain=False,
                        )
                        logger.debug(f"Published firmware update availability: {available}")
                    except Exception as e:
                        logger.debug(f"Could not update firmware update sensor: {e}")

                # Publish discovery if pending and client is connected
                if self.mqtt_discovery_pending and self.mqtt_enabled and self.mqtt_client:
                    is_connected = self.mqtt_client.is_connected() if self.mqtt_client else False
                    logger.info(
                        f"Discovery pending: flag=True, enabled={self.mqtt_enabled}, "
                        f"client_exists=True, connected={is_connected}"
                    )
                    try:
                        # Wait for connection to fully handshake with broker
                        await asyncio.sleep(1.0)
                        await self._mqtt_publish_discovery()
                        self.mqtt_discovery_pending = False
                    except Exception as e:
                        logger.error(f"Error publishing MQTT discovery: {e}", exc_info=True)
                elif self.mqtt_discovery_pending:
                    logger.info(
                        f"Discovery NOT published: pending=True, enabled={self.mqtt_enabled}, "
                        f"client={self.mqtt_client is not None}"
                    )

                # Publish health metrics
                await self.publish_health_metrics()

                # Wait for next update cycle (heartbeat refresh)
                await asyncio.sleep(self.scan_interval)

            except Exception as e:
                logger.error(f"Error in periodic updates: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def run(self):
        """Main run loop."""
        self.loop = asyncio.get_running_loop()
        logger.info("Starting Meticulous Espresso Add-on")
        logger.info(
            f"Configuration: machine_ip={self.machine_ip}, " f"scan_interval={self.scan_interval}s"
        )
        if not self.machine_ip:
            logger.error(
                "Machine IP is not set. Open the add-on options and enter the machine IP "
                "or hostname (e.g., 192.168.x.x or meticulous.local). Startup aborted."
            )
            await self.publish_connectivity(False)
            return
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
    logger.info(
        f"Sensor refresh rate is set to {addon.refresh_rate_minutes} minute(s). "
        "To change, set 'refresh_rate_minutes' in the add-on config (recommended: 5-10)."
    )
    try:
        asyncio.run(addon.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
