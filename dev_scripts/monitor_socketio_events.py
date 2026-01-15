

#!/usr/bin/env python3
"""Manual developer tool: Monitors and logs all Socket.IO events from the espresso machine for debugging and development purposes."""
import logging
import time
from typing import Any, Dict

from meticulous.api import Api, ApiOptions

# Setup logging to see everything
logging.basicConfig(
	level=logging.DEBUG,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Machine IP
MACHINE_IP = "192.168.0.115"
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
	logger.info(f"[PROFILE CHANGE #{event_counts['profile_change']}] {profile}")

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
		logger.info(f"Device: {device_info.name}")
		logger.info(f"Serial: {device_info.serial}")
		logger.info(f"Firmware: {device_info.firmware}")
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

if __name__ == "__main__":
	main()
