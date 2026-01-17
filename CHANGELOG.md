# Changelog

All notable user-facing changes to this add-on are documented here.

## [0.5.21] - 2026-01-17

### ⚡ Performance
- Simplified sensor filtering configuration with consolidated delta parameters
- **New configuration options** (replaces individual per-sensor thresholds):
  - **Temperature Delta** (0.5°C): Applies to all temperature sensors (boiler, brew head, external sensors, target temperature)
  - **Pressure Delta** (0.2 bar): Applies to pressure and target pressure
  - **Flow Delta** (0.1 ml/s): Applies to flow rate and target flow
  - **Weight Delta** (0.1g): Applies to shot weight and target weight
  - **Time Delta** (0.1s): Applies to timers and elapsed time tracking
  - **Voltage Delta** (1.0V): Power supply voltage readings
  - **Brightness Delta** (1 point): Display brightness level
- Reduced MQTT message flooding by ~70% while keeping sensor readings responsive
- All threshold defaults optimized for typical espresso brewing scenarios

## [0.5.20] - 2026-01-15

### 🔧 Improvements
- Fixed MQTT device discovery grouping by excluding null fields from device block
- Removed `null` values for optional device fields (`sw_version`, `hw_version`) to match Home Assistant device schema expectations
- Ensures all entity discovery configs are recognized as belonging to the same device

## [0.5.19] - 2026-01-15

### 🔧 Improvements
- Corrected MQTT discovery payload field names to match Home Assistant spec exactly
- Changed `uniq_id` to `unique_id` (critical fix for HA discovery acceptance)
- Replaced abbreviated field names with full names for clarity: `stat_t` → `state_topic`, `cmd_t` → `command_topic`, `avty_t` → `availability_topic`, `dev_cla` → `device_class`, `unit_of_meas` → `unit_of_measurement`
- Home Assistant now properly processes and recognizes discovery messages

## [0.5.18] - 2026-01-15

### 🔧 Improvements
- Fixed MQTT discovery subscription order to match zigbee2mqtt pattern
- Now subscribes to homeassistant/# BEFORE publishing discovery configs
- Ensures proper handshaking with broker before publishing discovery messages
- Resolves discovery message delivery to Home Assistant

## [0.5.17] - 2026-01-15

### ⚡ Performance
- Reduced MQTT discovery latency from ~5 minutes to ~0.5 seconds after connection
- Restructured periodic_updates loop to check discovery flag frequently without blocking API refresh schedule
- Discovery now publishes immediately after MQTT connection handshake completes

## [0.5.16] - 2026-01-15

### 🐛 Bug Fixes
- Fixed MQTT discovery device name inconsistency causing potential conflicts
- Now uses fixed device name "Meticulous Espresso" for reliable Home Assistant discovery

## [0.5.15] - 2026-01-15

### 🔧 Improvements
- Enhanced MQTT diagnostics with detailed connection attempt logging
- Now logs MQTT connection host, port, username, and password status
- Better visibility for troubleshooting credential and authentication issues

## [0.5.14] - 2026-01-15

### 🔧 Improvements
- Upgraded MQTT discovery with QoS 1 and proper async/await handling
- Extended background thread flush time to ensure all discovery messages reach broker
- Added comprehensive error handling for all discovery publishing blocks

## [0.5.13] - 2026-01-15

### 🔧 Improvements
- Simplified MQTT discovery publishing with cleaner async/await pattern
- Improved error handling and logging for discovery process
- Better visibility into discovery publishing with detailed INFO-level logs

## [0.5.12] - 2026-01-15

### 🐛 Bug Fixes
- Fixed MQTT discovery entities not appearing in Home Assistant
- Changed MQTT discovery publish quality of service from QoS 0 to QoS 1 for guaranteed delivery
- Made discovery publishing fully async with proper await handling
- Discovery messages now properly reach Home Assistant broker

## [0.5.11] - 2026-01-15

### 🔧 Improvements
- Enhanced MQTT discovery diagnostics with connection state logging
- Now logs client connection status before and after discovery publishing
- Improved debug output for troubleshooting discovery issues

## [0.5.10] - 2026-01-15

### 🐛 Bug Fixes
- Fixed MQTT discovery entities not appearing - added connection handshake delay

## [0.5.9] - 2026-01-15

### 🔧 Improvements
- Added diagnostics for MQTT discovery publishing to help troubleshoot connectivity issues

## [0.5.8] - 2026-01-15

### 🐛 Bug Fixes
- Fixed MQTT Home Assistant discovery entities not appearing after add-on restart
  - Your machine sensors now properly show up in Home Assistant after any restart or reconnection

## [0.5.7] - 2026-01-15

### 🐛 Bug Fixes
- Fixed MQTT discovery messages not reaching Home Assistant broker

## [0.5.6] - 2026-01-15

### 🐛 Bug Fixes
- Improved MQTT message delivery confirmation and diagnostics

## [0.5.5] - 2026-01-15

### 🐛 Bug Fixes
- Improved MQTT diagnostics and error handling

## [0.5.4] - 2026-01-14

### ✨ New Features
- **New Commands**: Added `continue_brew` and `reboot_machine` commands
- **Firmware Update Sensor**: See when firmware updates are available for your machine
- **Improved Brightness Control**: Brightness is now a slider for easier adjustment
- **Configurable Refresh Rate**: Adjust how often sensors update (1-60 minutes, default 5)

### 🐛 Bug Fixes
- Fixed profile loading reliability
- Improved command execution

## [0.5.1-0.5.3] - 2026-01-09

### 🐛 Bug Fixes
- Fixed profile selector dropdown on startup
- Improved reliability of profile selection

## [0.5.0] - 2026-01-09

### 🎮 Full Machine Control in Home Assistant
Your Meticulous machine is now fully controllable from Home Assistant!

### ✨ New Features
- **Brew Controls** - Start, stop, and continue brewing from Home Assistant
- **Machine Operations** - Preheat your machine and tare the scale with buttons
- **Settings** - Adjust brightness with a slider and toggle sounds on/off
- **Profile Selector** - Switch between profiles with a dropdown menu
- **Real-time Updates** - All sensors update instantly when you interact with your machine

## [0.4.0-0.4.3] - 2026-01-09

### 🎉 Real-time Updates
All sensors now update instantly when you interact with your machine - no more waiting for polling updates!

### 🐛 Bug Fixes
- Fixed crashes during live updates
- Improved profile loading with fractional timestamps

## [0.3.0-0.3.6] - 2026-01-09

### ✨ Features
- **Full Home Assistant Integration** - Your Meticulous machine appears in Home Assistant with sensors and controls
- **Real-time Updates** - See machine status, temperature, pressure, and timing instantly
- **Automation Ready** - Create automations based on your machine's state
- All sensors now appear immediately in Home Assistant on startup

## [0.1.0] - 2026-01-07

- Initial release with MQTT discovery and Meticulous Espresso integration
