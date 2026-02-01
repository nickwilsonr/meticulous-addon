# Architecture & Integration Guide

**For:** Developers and technical contributors
**Audience:** Contributors, maintainers, developers wanting to extend the add-on

## Overview

The Meticulous Home Assistant add-on provides real-time integration with Meticulous Espresso machines via Socket.IO and MQTT discovery. This document covers the architecture, implementation details, sensor/command specifications, and integration strategy.

---

## Completed Features

### Core Architecture
✅ **Socket.IO Real-time Updates**: Event handlers for status, temperature, profile changes, and notifications
✅ **MQTT Discovery**: Auto-entity creation for 25+ sensors with device_class, units, and availability tracking
✅ **MQTT Command Interface**: 8 service commands via MQTT topics
✅ **Exponential Backoff**: Resilient reconnection with configurable jitter
✅ **Health Metrics**: Diagnostic data publishing (uptime, reconnect count, error tracking)
✅ **Graceful Degradation**: Availability topic with online/offline states

### Sensors (25 total)
- **Machine Status**: connected, state, brewing, preheat_remaining
- **Temperature**: boiler, brew head, target, external_temp_1, external_temp_2
- **Brewing**: pressure, flow rate, shot timer, shot weight, target weight
- **Profile**: active profile name, author
- **Settings**: sounds enabled, brightness
- **Statistics**: total shots, last shot name/rating/time
- **Device**: firmware version, software version, voltage

### Commands (8 total via MQTT)
- `meticulous_espresso/command/start_brew`
- `meticulous_espresso/command/stop_brew`
- `meticulous_espresso/command/continue_brew`
- `meticulous_espresso/command/preheat`
- `meticulous_espresso/command/tare_scale`
- `meticulous_espresso/command/load_profile` (payload: profile_id)
- `meticulous_espresso/command/set_brightness` (payload: 0-100 or JSON)
- `meticulous_espresso/command/enable_sounds` (payload: true/false)

### Configuration Options
- **Machine**: `machine_ip` (IP or hostname)
- **Filtering**: `enable_delta_filtering` (true/false), temperature/pressure/flow/weight/time/voltage deltas
- **Refresh**: `stale_data_refresh_interval` (1-168 hours, default 24)
- **MQTT**: `mqtt_enabled`, `mqtt_host`, `mqtt_port`, `mqtt_username`, `mqtt_password`
- **Logging**: `debug` (boolean)

## File Structure

```
meticulous-addon/
├── config.yaml                    # Add-on metadata & schema
├── Dockerfile                     # Multi-arch container build
├── build.json                     # Architecture-specific base images
├── requirements.txt               # Python dependencies
├── rootfs/
│   └── usr/
│       └── bin/
│           ├── run.py            # Main application (688 lines)
│           └── mqtt_commands.py  # Command handlers (160 lines)
├── translations/
│   └── en.json                   # UI field descriptions
├── docs/                          # Documentation hub
└── .github/
	└── workflows/
		└── builder.yml           # CI/CD for multi-arch images
```

## Key Implementation Details

### Socket.IO Event Handlers
- `_handle_status_event(StatusData)`: Real-time state, sensors (p/f/w/t), brewing flag, shot timer
- `_handle_temperature_event(Temperatures)`: Boiler and brew head temperatures
- `_handle_profile_event`: Triggers profile info refresh
- `_handle_notification_event`: Logs and forwards to HA notifications

### MQTT Discovery
- Published to `homeassistant/{component}/{object_id}/config`
- Includes device info (identifiers, manufacturer, model, versions)
- Sets availability topic for graceful degradation
- Adds device_class (temperature, pressure, voltage) and units (°C, bar, V, s, g, %)

### MQTT Commands
- Subscribed to `meticulous_espresso/command/#`
- Callback `mqtt_on_message` parses topic and dispatches to handler
- Handlers execute Meticulous API calls (ActionType enum)
- Triggers sensor updates (update_profile_info, update_settings) after state changes

### Health Metrics
- Published to `meticulous_espresso/health` every stale_data_refresh_interval or periodic update
- Tracks: uptime_seconds, reconnect_count, last_error, last_error_time, api_connected, socket_connected
- Updated on reconnection failures in `maintain_socket_connection`

### Retry Logic
- `_compute_backoff(attempt)`: min(retry_max, retry_initial * (2 ** (attempt-1))) + jitter
- Jitter: 0-20% random to prevent thundering herd
- Used in `maintain_socket_connection` for Socket.IO reconnect

### Polling Updates
- `update_profile_info()`: get_last_profile() → active_profile, profile_author, target_temperature, target_weight
- `update_statistics()`: get_history_statistics(), get_last_shot() → total_shots, last_shot_*
- `update_settings()`: get_settings() → sounds_enabled (brightness from temperature events)
- Runs periodically (frequency based on stale_data_refresh_interval)

---

## Integration Strategy: Sensors & Controls

### Philosophy

Focus on home automation use cases rather than exposing the full API. Provide actionable data and controls that make sense in a smart home context.

### Sensors (24 total)

**Sensor Categories & Update Strategy:**

Sensors are categorized by update frequency and data type to determine optimal publishing strategy:

- **High-Frequency Floating Point** (require delta-based throttling): Temperature, pressure, flow rate, weight, timers
  - Updates during brewing are very frequent (~100Hz from Socket.IO)
  - Delta thresholds prevent MQTT message flooding
  - Recommended: 0.1-1.0°C, 0.2 bar, 0.1 ml/s, 0.1g, 1.0s thresholds

- **Low-Frequency State Changes** (exact match detection): State, profile, brewing flag, connectivity, settings
  - Update infrequently and should publish on any change
  - No delta filtering needed

- **Medium-Frequency** (moderate delta): Voltage (1.0V threshold)

- **Rarely-Changing Targets**: Target temperature, weight, pressure (publish on any change)

**Sensor List:**
- `sensor.meticulous_connected`: Connection status (binary)
- `sensor.meticulous_state`: Current machine state (Idle, Preheating, Heating, Brewing, Purging, Retracting, Closing Valve, Home, Booting, Starting)
- `binary_sensor.meticulous_brewing`: Extraction active flag (binary)
- `sensor.meticulous_preheat_remaining`: Time remaining for preheating in seconds

**Temperature** (5 sensors)
- `sensor.meticulous_boiler_temperature`: Boiler temp (device_class: temperature)
- `sensor.meticulous_brew_head_temperature`: Brew head temp (device_class: temperature)
- `sensor.meticulous_external_temp_1`: External temperature sensor 1 (device_class: temperature)
- `sensor.meticulous_external_temp_2`: External temperature sensor 2 (device_class: temperature)
- `sensor.meticulous_target_temperature`: Profile target temp (device_class: temperature)

**Brewing** (6 sensors)
- `sensor.meticulous_shot_timer`: Shot elapsed time (seconds)
- `sensor.meticulous_pressure`: Current pressure (bar)
- `sensor.meticulous_flow_rate`: Current flow rate (ml/s)
- `sensor.meticulous_shot_weight`: Current weight on scale (grams)
- `sensor.meticulous_target_weight`: Profile target weight (grams)

**Profile** (2 sensors)
- `sensor.meticulous_active_profile`: Loaded profile name
- `sensor.meticulous_profile_author`: Profile author

**Settings** (2 sensors)
- `sensor.meticulous_brightness`: Display brightness (0-100)
- `binary_sensor.meticulous_sounds_enabled`: Sound state

**Statistics** (3 sensors)
- `sensor.meticulous_total_shots`: Lifetime shot count
- `sensor.meticulous_last_shot_name`: Last shot name
- `sensor.meticulous_last_shot_rating`: Last shot rating (like/dislike/null)

**Device Info** (3 sensors)
- `sensor.meticulous_firmware_version`: Firmware version
- `sensor.meticulous_software_version`: Software version
- `sensor.meticulous_voltage`: Power supply voltage (device_class: voltage)

**Connectivity** (1 sensor)
- `binary_sensor.meticulous_connected`: Connection status (device_class: connectivity)

### Commands (MQTT)

- **Brewing**: `start_brew`, `stop_brew`, `continue_brew`
- **Machine**: `preheat`, `tare_scale`
- **Profiles**: `load_profile` (profile_id payload)
- **Settings**: `set_brightness` (0-100 or JSON), `enable_sounds` (true/false), `toggle_sounds`

Each service has a corresponding sensor to verify the change.

### Entity Structure

```yaml
Device:
  name: "Meticulous Espresso Machine"
  identifiers: [[meticulous, <serial>]]
  manufacturer: "Meticulous"
  model: <model_version>
  sw_version: <firmware>
```

### Data Flow

```
Machine API (Port 8080)
  ↓
Socket.IO Events (real-time) + REST API (polling)
  ↓
Add-on Python Application
  ↓
Home Assistant (MQTT discovery)
  ↓
Automations & Dashboard
```

### Socket.IO Events (Priority)

1. **onStatus** (CRITICAL): state, extracting, time, sensors (p, f, w, t)
2. **onTemperatureSensors** (HIGH): All temperature sensors
3. **onProfileChange** (MEDIUM): Profile loaded/changed
4. **onSettingsChange** (MEDIUM): Settings modified
5. **onNotification** (MEDIUM): Machine alerts

### Update Strategy

- Real-time: Use Socket.IO for brewing sensors, temperatures
- Polling: Profile info (on change), statistics (5-10 min), device info (30 min), settings (60s)
- Connection: Graceful degradation with exponential backoff reconnection

### Excluded Features (Intentionally)

- WiFi management (configure via machine)
- Firmware updates (critical, local only)
- Calibration (requires physical interaction)
- Profile creation/editing (dedicated app better)
- Timezone management (auto-sync recommended)

---

## Next Steps

See [docs/development.md](development.md) for setup, testing, and roadmap.

## Documentation Index

- [Automations Examples](automations.md)
- [MQTT Topics Reference](mqtt-topics.md)
- [Developer Guide](development.md)
