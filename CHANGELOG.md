# Changelog

All notable user-facing changes to this add-on are documented here.

## [0.26.9] - 2026-01-26

### 📝 Improvements
- **Reduced debug logging chattiness** - Removed excessive Socket.IO event logging that was unreadable (hundreds of packets per second). Only meaningful state changes logged now (machine state, profile changes, errors)

## [0.26.8] - 2026-01-26

### 🔧 Fixes
- **Fixed brightness 1-behind lag** - Skip brightness in Socket.IO settings handler to prevent retained messages from overwriting immediate command publish
- **Initialize brightness on startup** - Set brightness to 50% on addon startup to sync machine and Home Assistant slider

## [0.26.7] - 2026-01-26

### 🔧 Fixes
- **Fixed brightness state publishing** - Publish brightness updates without retain flag to update UI while avoiding feedback loops from stale retained messages

## [0.26.6] - 2026-01-26

### 🔧 Fixes
- **Fixed brightness command lag** - Removed immediate state publish that was creating MQTT feedback loop causing commands to execute one step behind

## [0.26.5] - 2026-01-26

### 🔧 Fixes
- **Pinned pymeticulous to 0.3.1** - Fixed version mismatch where container could install 0.3.0 with validation bugs

## [0.26.4] - 2026-01-26

### 🔧 Fixes
- **Action response status checking** - Fixed action handlers to properly check ActionResponse.status, catching when machine rejects actions (e.g., can't tare while extracting)
- **Brightness normalization** - Fixed brightness value conversion to use proper float type for API validation

## [0.26.3] - 2026-01-26

### 🔧 Fixes
- **Actions now working** - Fixed espresso machine actions (start brew, stop, preheat, tare, etc.) that were not executing
- **Profile selection fixed** - Profile hover selection now works correctly
- **Updated to latest pyMeticulous 0.3.1** - Now using the latest version of the pyMeticulous library with bug fixes

## [0.26.2] - 2026-01-20

### ✨ Improvements
- **Automatic entity cleanup on startup** - Add-on now automatically clears stale Home Assistant entities on each upgrade, ensuring a clean slate without manual intervention
- **Cleaner logs** - Reduced verbosity in startup logs by moving diagnostic details to debug level

## [0.26.1] - 2026-01-20

### 🔧 Improvements
- Improved logging to help diagnose sensor issues
- Fixed connection timing to ensure proper initialization

## [0.26.0] - 2026-01-20

### ✨ Fixes
- **All sensors now display properly** - Fixed issues where Brewing, Connected, and other binary sensors showed as "unknown"
- **Fixed brightness control** - No longer appears as duplicate sensor
- **Fixed sounds toggle** - Now appears correctly in Home Assistant
- **Fixed active profile selector** - Shows the currently selected profile
- **Improved startup** - All sensor values load immediately when the add-on starts
- Updated to pyMeticulous 0.3.1 for better API reliability

## [0.5.25] - 2026-01-20

### 🔍 Improvements
- Added better diagnostics to help troubleshoot sensor visibility issues

## [0.5.24] - 2026-01-20

### ⚙️ Improvements
- Updated core machine communication for better reliability

## [0.5.23] - 2026-01-17

### 🐛 Bug Fixes
- Fixed profile selector not showing your current choice
- All machine values now load immediately when the add-on starts
- Fixed sounds and brightness controls appearing correctly in Home Assistant

## [0.5.22] - 2026-01-17

### 🐛 Bug Fixes
- Fixed sensors showing "unknown" when they should show real values
- All machine information loads properly at startup

## [0.5.21] - 2026-01-17

### ⚡ Performance
- Reduced unnecessary sensor messages - your network stays quieter while sensors still update responsively
- New settings let you control how often sensors refresh

## [0.5.20] - 2026-01-15

### 🔧 Improvements
- Fixed how your machine appears as a device in Home Assistant

## [0.5.19] - 2026-01-15

### 🔧 Improvements
- Fixed how Home Assistant recognizes the add-on

## [0.5.18] - 2026-01-15

### 🔧 Improvements
- Improved connection handshake with Home Assistant

## [0.5.17] - 2026-01-15

### ⚡ Performance
- Sensors now appear in Home Assistant much faster after startup

## [0.5.16] - 2026-01-15

### 🐛 Bug Fixes
- Fixed device name consistency in Home Assistant

## [0.5.15] - 2026-01-15

### 🔧 Improvements
- Better diagnostic information for troubleshooting connection issues

## [0.5.14] - 2026-01-15

### 🔧 Improvements
- Improved sensor discovery reliability

## [0.5.13] - 2026-01-15

### 🔧 Improvements
- Better error handling for sensor discovery

## [0.5.12] - 2026-01-15

### 🐛 Bug Fixes
- Fixed sensors not appearing in Home Assistant after starting the add-on

## [0.5.11] - 2026-01-15

### 🔧 Improvements
- Better diagnostics for connection troubleshooting

## [0.5.10] - 2026-01-15

### 🐛 Bug Fixes
- Fixed sensors not appearing after startup

## [0.5.9] - 2026-01-15

### 🔧 Improvements
- Added troubleshooting information for sensor discovery

## [0.5.8] - 2026-01-15

### 🐛 Bug Fixes
- Fixed sensors disappearing after add-on restart - they now reappear properly in Home Assistant

## [0.5.7] - 2026-01-15

### 🐛 Bug Fixes
- Fixed sensors not reaching Home Assistant

## [0.5.6] - 2026-01-15

### 🐛 Bug Fixes
- Improved message delivery to Home Assistant

## [0.5.5] - 2026-01-15

### 🐛 Bug Fixes
- Improved connection reliability

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
