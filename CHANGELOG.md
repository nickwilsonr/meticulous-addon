# Changelog

All notable user-facing changes to this add-on are documented here.
## [0.5.3] - 2026-01-09

### Bug Fix
- Fixed profile selector dropdown - corrected API endpoint to fetch available profiles

## [0.5.2] - 2026-01-09

### Improvements
- Profile selector now appears reliably on startup
- Reduced unnecessary log messages
- More efficient real-time updates (uses Socket.IO events instead of polling)

## [0.5.1] - 2026-01-09

### Bug Fix
- Fixed missing profile selector dropdown on startup

## [0.5.0] - 2026-01-09

### 🎮 Full Machine Control in Home Assistant
Your Meticulous machine is now fully controllable from Home Assistant! All essential brewing operations appear as buttons and controls.

### ✨ New Features
- **Brew Controls** - Start, stop, and continue brewing directly from Home Assistant
- **Machine Operations** - Preheat your machine and tare the scale with dedicated buttons
- **Settings** - Adjust brightness with a slider and toggle sounds on/off
- **Profile Selector** - Switch between profiles with a simple dropdown (auto-updates when profiles are added/deleted)
- **Real-time Updates** - Sensors update instantly when you interact with your machine (no more waiting for polling)

### 🔧 Technical Improvements
- Auto-refreshes profile list when profiles are added or deleted on the machine
- Better error messaging when machine IP is not configured
- More stable Socket.IO connection handling

## [0.4.3] - 2026-01-09

### Bug Fixes
- Fixed profile info loading when the machine reports fractional timestamps
- Show a clear error and stop startup if the machine IP is not set

## [0.4.2] - 2026-01-09

### Bug Fix
- Fixed crashes during live updates


## [0.4.1] - 2026-01-09

### Bug Fix
- Fixed excessive logging that could overwhelm the system

## [0.4.0] - 2026-01-09

### 🎉 Real-time updates now work!
All sensors now update instantly when you interact with your machine - profile changes, shot weight, temperatures, and machine state all reflect immediately in Home Assistant.

### What's Fixed
- Sensors update in real-time instead of staying "unknown"
- Profile changes on the machine now update the active profile sensor
- Shot weight tracks live during brewing
- Temperature sensors update continuously

## [0.3.6] - 2026-01-09

### ✨ Improvements
- **More sensors available immediately** - Profile author and last shot details (name, profile, rating, time) now appear as soon as the add-on starts
- **Better sensor coverage** - Added 5 new sensors that were missing from MQTT discovery
- **Smarter startup** - The add-on now fetches all available sensor data at startup instead of waiting for updates

### 🐛 Bug Fixes
- Fixed sensors that would show "unknown" until the machine was actively used
- Corrected sensor discovery to match documented sensor list

### 📝 Note
- Some sensors (pressure, flow, temperatures) only update when the machine is actively brewing, as they're only available via real-time Socket.IO events
- Brightness sensor will show "unknown" until explicitly set (API limitation)

## [0.3.5] - 2026-01-09

### 🐛 Bug Fixes
- Fixed MQTT connection issues
- Cleaned-up documentation and configuration references

## [0.3.4] - 2026-01-09

### 🐛 Bug Fixes
- Fixed MQTT connection timing issue preventing sensors from appearing in Home Assistant

## [0.3.3] - 2026-01-09

### ✨ Features
- All sensors now publish initial state on startup (T0 snapshot)
- All entities appear immediately in Home Assistant instead of waiting for updates

### 🐛 Bug Fixes
- Fixed missing sensor mappings (external temperatures, total shots now visible)

## [0.3.2] - 2026-01-09

### 🐛 Bug Fixes
- Improved diagnostic logging

## [0.3.1] - 2026-01-09

### 🐛 Bug Fixes
- Fixed MQTT connectivity issues
- Improved reliability

## [0.3.0] - 2026-01-09

### ✨ What's New
- **Full Home Assistant Integration** - Your Meticulous machine now appears in Home Assistant with all sensors and controls
- **Real-time Updates** - See machine status, temperature, pressure, and shot timing instantly
- **Automation Ready** - Create automations and routines based on your machine's state

### 🐛 Fixes
- Fixed MQTT connectivity issues preventing sensors from appearing
- Improved startup reliability and error handling
- Better firmware compatibility

## [0.2.x] - 2026-01-09

- Fixed startup and stability issues
- Improved security and compatibility
- Simplified configuration

## [0.1.0] - 2026-01-07

- Initial release with MQTT discovery and Meticulous Espresso integration
