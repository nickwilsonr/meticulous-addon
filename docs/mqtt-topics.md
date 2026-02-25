# MQTT Topics Reference

**For:** End-users and developers
**Audience:** Anyone integrating via MQTT

---

## Discovery Topics

Published once on connect to `homeassistant/{component}/{object_id}/config`:

```
homeassistant/binary_sensor/meticulous_espresso_connected/config
homeassistant/binary_sensor/meticulous_espresso_brewing/config
homeassistant/sensor/meticulous_espresso_state/config
homeassistant/sensor/meticulous_espresso_boiler_temperature/config
homeassistant/sensor/meticulous_espresso_brew_head_temperature/config
homeassistant/sensor/meticulous_espresso_external_temp_1/config
homeassistant/sensor/meticulous_espresso_external_temp_2/config
homeassistant/sensor/meticulous_espresso_pressure/config
homeassistant/sensor/meticulous_espresso_flow_rate/config
homeassistant/sensor/meticulous_espresso_shot_timer/config
homeassistant/sensor/meticulous_espresso_shot_weight/config
homeassistant/sensor/meticulous_espresso_target_weight/config
homeassistant/sensor/meticulous_espresso_active_profile/config
homeassistant/sensor/meticulous_espresso_profile_author/config
homeassistant/sensor/meticulous_espresso_target_temperature/config
homeassistant/sensor/meticulous_espresso_firmware_version/config
homeassistant/sensor/meticulous_espresso_software_version/config
homeassistant/sensor/meticulous_espresso_voltage/config
homeassistant/switch/meticulous_espresso_sounds_enabled/config
homeassistant/sensor/meticulous_espresso_brightness/config
homeassistant/number/meticulous_espresso_brightness/config
homeassistant/select/meticulous_espresso_active_profile/config
homeassistant/sensor/meticulous_espresso_total_shots/config
homeassistant/sensor/meticulous_espresso_last_shot_name/config
homeassistant/sensor/meticulous_espresso_last_shot_rating/config
homeassistant/sensor/meticulous_espresso_last_shot_time/config
homeassistant/image/meticulous_espresso_active_profile_image/config
homeassistant/sensor/meticulous_espresso_active_profile_filename/config
```

## State Topics

Published on updates to `meticulous_espresso/sensor/{key}/state`:

```
meticulous_espresso/sensor/connected/state              → true/false
meticulous_espresso/sensor/state/state                  → idle/brewing/heating/steaming/preheating/error
meticulous_espresso/sensor/brewing/state                → true/false
meticulous_espresso/sensor/boiler_temperature/state     → 93.2
meticulous_espresso/sensor/brew_head_temperature/state  → 92.8
meticulous_espresso/sensor/external_temp_1/state        → 25.5
meticulous_espresso/sensor/external_temp_2/state        → 26.1
meticulous_espresso/sensor/pressure/state               → 9.5
meticulous_espresso/sensor/flow_rate/state              → 2.3
meticulous_espresso/sensor/shot_timer/state             → 28.5
meticulous_espresso/sensor/shot_weight/state            → 36.2
meticulous_espresso/sensor/target_weight/state          → 36.0
meticulous_espresso/sensor/target_temperature/state     → 93.0
meticulous_espresso/sensor/active_profile/state         → "Morning Blend"
meticulous_espresso/sensor/profile_author/state         → "Barista Joe"
meticulous_espresso/sensor/firmware_version/state       → "1.2.3"
meticulous_espresso/sensor/software_version/state       → "2.1.0"
meticulous_espresso/sensor/voltage/state                → 120
meticulous_espresso/sensor/sounds_enabled/state         → true/false
meticulous_espresso/sensor/brightness/state             → 75
meticulous_espresso/sensor/total_shots/state            → 1234
meticulous_espresso/sensor/last_shot_name/state         → "Espresso"
meticulous_espresso/sensor/last_shot_rating/state       → "like"
meticulous_espresso/sensor/last_shot_time/state         → "2024-01-15T10:30:00"
meticulous_espresso/sensor/active_profile_image/state    → <binary PNG image data>
meticulous_espresso/sensor/active_profile_filename/state → "abc123.jpg"
meticulous_espresso/profiles                             → [{"profile_id": "...", "name": "...", "image_filename": "..."}]
```

## Command Topics

Subscribe to `meticulous_espresso/command/#`:

### Simple Commands (no payload)
```
meticulous_espresso/command/start_shot      → Start a shot (load & execute profile)
meticulous_espresso/command/stop_shot       → Stop the plunger immediately mid-shot
meticulous_espresso/command/continue_shot   → Resume a paused shot
meticulous_espresso/command/preheat         → Preheat water in chamber to target temperature
meticulous_espresso/command/tare_scale      → Zero the scale
meticulous_espresso/command/abort_shot      → Abort current profile and retract plunger
meticulous_espresso/command/home_plunger    → Reset plunger to home position
meticulous_espresso/command/purge           → Flush water through group head
```

### Commands with Payload
```
meticulous_espresso/command/load_profile
	Payload: "profile-id-string"

meticulous_espresso/command/set_brightness
	Payload (simple): "75"
	Payload (advanced): {"brightness": 75, "interpolation": "curve", "animation_time": 500}

meticulous_espresso/command/enable_sounds
	Payload: "true" | "false" | "1" | "0" | "on" | "off" | "yes" | "no"
```

## Availability Topic

Published on connect/disconnect to `meticulous_espresso/availability`:
```
meticulous_espresso/availability → "online" | "offline"
```

All discovered entities use this as their availability topic.

## Health Topic

Published periodically to `meticulous_espresso/health`:
```json
{
	"uptime_seconds": 3600,
	"reconnect_count": 2,
	"last_error": "Connection timeout",
	"last_error_time": "2024-01-15T10:30:00",
	"api_connected": true,
	"socket_connected": true
}
```

## Home Assistant Automation Examples

### Start Shot at 7 AM
```yaml
automation:
	- alias: "Morning coffee"
		trigger:
			- platform: time
				at: "07:00:00"
		action:
			- service: mqtt.publish
				data:
					topic: meticulous_espresso/command/start_shot
```

### Load Profile Based on Day
```yaml
automation:
	- alias: "Weekend profile"
		trigger:
			- platform: time
				at: "08:00:00"
		condition:
			- condition: time
				weekday:
					- sat
					- sun
		action:
			- service: mqtt.publish
				data:
					topic: meticulous_espresso/command/load_profile
					payload: "weekend-blend-profile-id"
```

### Dim Display at Night
```yaml
automation:
	- alias: "Dim espresso display at night"
		trigger:
			- platform: time
				at: "22:00:00"
		action:
			- service: mqtt.publish
				data:
					topic: meticulous_espresso/command/set_brightness
					payload: "20"
	- alias: "Restore display brightness in morning"
		trigger:
			- platform: time
				at: "06:00:00"
		action:
			- service: mqtt.publish
				data:
					topic: meticulous_espresso/command/set_brightness
					payload: "80"
```

### Notify on Connection Loss
```yaml
automation:
	- alias: "Espresso machine offline alert"
		trigger:
			- platform: mqtt
				topic: meticulous_espresso/availability
				payload: "offline"
		action:
			- service: notify.mobile_app
				data:
					message: "Espresso machine has gone offline"
```

### Monitor Health Metrics
```yaml
sensor:
	- platform: mqtt
		name: "Espresso Add-on Uptime"
		state_topic: "meticulous_espresso/health"
		value_template: "{{ value_json.uptime_seconds / 3600 | round(1) }}"
		unit_of_measurement: "hours"

	- platform: mqtt
		name: "Espresso Add-on Reconnects"
		state_topic: "meticulous_espresso/health"
		value_template: "{{ value_json.reconnect_count }}"
```

## Testing Commands via CLI

Using `mosquitto_pub` from the command line:

```bash
# Start shot
mosquitto_pub -h localhost -t meticulous_espresso/command/start_shot -m ""

# Stop shot
mosquitto_pub -h localhost -t meticulous_espresso/command/stop_shot -m ""

# Abort shot
mosquitto_pub -h localhost -t meticulous_espresso/command/abort_shot -m ""

# Home plunger
mosquitto_pub -h localhost -t meticulous_espresso/command/home_plunger -m ""

# Purge group head
mosquitto_pub -h localhost -t meticulous_espresso/command/purge -m ""

# Set brightness
mosquitto_pub -h localhost -t meticulous_espresso/command/set_brightness -m "75"

# Enable sounds
mosquitto_pub -h localhost -t meticulous_espresso/command/enable_sounds -m "true"

# Load profile
mosquitto_pub -h localhost -t meticulous_espresso/command/load_profile -m "my-profile-id"
```

## Monitoring via CLI

```bash
# Watch all sensor updates
mosquitto_sub -h localhost -t "meticulous_espresso/sensor/#" -v

# Watch availability
mosquitto_sub -h localhost -t "meticulous_espresso/availability" -v

# Watch health metrics
mosquitto_sub -h localhost -t "meticulous_espresso/health" -v

# Watch all command topics (for debugging)
mosquitto_sub -h localhost -t "meticulous_espresso/command/#" -v
```
