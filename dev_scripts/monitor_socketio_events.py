

# !/usr/bin/env python3
"""Manual developer tool: Monitors and logs all Socket.IO events.

This tool monitors and logs Socket.IO events from the espresso machine
for debugging and development purposes.
"""
import logging
import sys
import time
from typing import Any, Dict

from meticulous.api import Api, ApiOptions

# Setup logging to file and console
log_file = "socketio_events.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Machine IP - read from command line or default
MACHINE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.115"
BASE_URL = f"http://{MACHINE_IP}"

# Event counters
event_counts = {
    "status": 0,
    "temperature": 0,
    "profile_change": 0,
    "notification": 0,
    "button": 0,
    "settings_change": 0,
    "communication": 0,
    "actuators": 0,
    "machine_info": 0,
}


def handle_status(status: Any):
    """Handle status events."""
    event_counts["status"] += 1
    logger.info(f"[STATUS #{event_counts['status']}] {status}")
    if hasattr(status, "state"):
        logger.info(f"  State: {status.state}")
    if hasattr(status, "extracting"):
        logger.info(f"  Extracting: {status.extracting}")
    if hasattr(status, "sensors"):
        logger.info(f"  Sensors: {status.sensors}")


def handle_temperature(temps: Any):
    """Handle temperature events."""
    event_counts["temperature"] += 1
    logger.info(f"[TEMPERATURE #{event_counts['temperature']}] {temps}")


def handle_profile_change(profile: Any):
    """Handle profile change events."""
    event_counts["profile_change"] += 1
    logger.info(f"[PROFILE CHANGE #{event_counts['profile_change']}]")
    logger.info(f"  Raw event: {profile}")
    logger.info(f"  Type: {type(profile)}")
    if hasattr(profile, "__dict__"):
        logger.info(f"  Attributes: {profile.__dict__}")
    if isinstance(profile, dict):
        for key, value in profile.items():
            logger.info(f"    {key}: {value}")


def handle_raw_event(event, *args):
    """Catch all Socket.IO events to ensure we don't miss anything."""
    logger.info(f"[RAW EVENT] name={event}, args={args}")


def handle_notification(notification: Any):
    """Handle notification events."""
    event_counts["notification"] += 1
    logger.info(f"[NOTIFICATION #{event_counts['notification']}] {notification}")


def handle_button(button: Any):
    """Handle button events."""
    event_counts["button"] += 1
    logger.info(f"[BUTTON #{event_counts['button']}] {button}")


def handle_settings_change(settings: Dict):
    """Handle settings change events."""
    event_counts["settings_change"] += 1
    logger.info(f"[SETTINGS CHANGE #{event_counts['settings_change']}] {settings}")


def handle_communication(comm: Any):
    """Handle communication events."""
    event_counts["communication"] += 1
    logger.info(f"[COMMUNICATION #{event_counts['communication']}] {comm}")


def handle_actuators(actuators: Any):
    """Handle actuator events."""
    event_counts["actuators"] += 1
    logger.info(f"[ACTUATORS #{event_counts['actuators']}] {actuators}")


def handle_machine_info(info: Any):
    """Handle machine info events."""
    event_counts["machine_info"] += 1
    logger.info(f"[MACHINE INFO #{event_counts['machine_info']}] {info}")


def main():
    """Run the test."""
    logger.info("=" * 80)
    logger.info("Socket.IO Event Monitor")
    logger.info(f"Connecting to: {BASE_URL}")
    logger.info(f"Logging to: {log_file}")
    logger.info("=" * 80)

    # Setup event handlers
    options = ApiOptions(
        onStatus=handle_status,
        onTemperatureSensors=handle_temperature,
        onProfileChange=handle_profile_change,
        onNotification=handle_notification,
        onButton=handle_button,
        onSettingsChange=handle_settings_change,
        onCommunication=handle_communication,
        onActuators=handle_actuators,
        onMachineInfo=handle_machine_info,
    )

    # Connect to API
    logger.info("Initializing API...")
    api = Api(base_url=BASE_URL, options=options)

    # Get device info
    logger.info("Fetching device info...")
    try:
        device_info = api.get_device_info()
        if device_info is not None and hasattr(device_info, "name"):
            name = getattr(device_info, "name", None)
            serial = getattr(device_info, "serial", None)
            firmware = getattr(device_info, "firmware", None)
            if name:
                logger.info(f"Device: {name}")
            if serial:
                logger.info(f"Serial: {serial}")
            if firmware:
                logger.info(f"Firmware: {firmware}")
        else:
            logger.warning(f"Could not fetch device info: {device_info}")
    except Exception as e:
        logger.warning(f"Could not fetch device info: {e}")

    # Connect Socket.IO
    logger.info("Connecting Socket.IO...")
    try:
        api.connect_to_socket()
        logger.info("Socket.IO connected!")
    except Exception as e:
        logger.error(f"Socket.IO connection failed: {e}")
        return

    # Register the catch-all handler AFTER Socket.IO is connected
    # Use explicit handler arg to avoid calling None when decorator isn't returned
    api.sio.on("*", handler=handle_raw_event)

    logger.info("=" * 80)
    logger.info("Listening for events... (Press Ctrl+C to stop)")
    logger.info("=" * 80)
    logger.info("")

    # Keep running and print summary every 5 seconds
    try:
        while True:
            time.sleep(5)
            total = sum(event_counts.values())
            if total > 0:
                logger.info("-" * 40)
                logger.info(f"Total events received: {total}")
                for event_type, count in event_counts.items():
                    if count > 0:
                        logger.info(f"  {event_type}: {count}")
                logger.info("-" * 40)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 80)
        logger.info("Stopping...")
        logger.info("Final event counts:")
        for event_type, count in event_counts.items():
            logger.info(f"  {event_type}: {count}")
        logger.info("=" * 80)
    finally:
        # Ensure Socket.IO connection is properly closed
        logger.info("Disconnecting Socket.IO...")
        try:
            api.disconnect_socket()
            logger.info("Socket.IO disconnected successfully")
        except Exception as e:
            logger.warning(f"Error disconnecting Socket.IO: {e}")

            if __name__ == "__main__":
                main()
