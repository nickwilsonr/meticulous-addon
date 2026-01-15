# Changelog

All notable user-facing changes to this add-on are documented here.

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
