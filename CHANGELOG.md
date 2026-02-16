# Changelog

All notable user-facing changes to this add-on are documented here.

## [0.31.2] - 2026-02-15

### Fixes
- **Startup shot timer reset** — Timer now resets to 0 when the add-on starts and the machine reports Idle, so a stale value from the previous shot isn’t published until an actual shot runs

## [0.31.0] - 2026-02-15

### Improvements
- **Profile selection sync** (by man on street) — Home Assistant profile dropdown now stays in sync when you change profiles via the machine's iOS app or other Socket.IO clients
- **Shot timer cleanup** — Timer automatically resets to 0 when the machine returns to Idle, preventing stale values from the previous shot

### Fixes
- **Profile state publishing** (by man on street) — Home Assistant now correctly receives profile state updates when you change profiles

## [0.30.8] - 2026-02-04

### Fixes
- **Preheat countdown precision** — Countdown timer now displays whole seconds without decimals (e.g., "45s" instead of "45.23s")

## [0.30.7] - 2026-02-04

### Fixes
- **Entity cleanup on upgrade** — Old sensors and entities from previous versions are now properly removed from Home Assistant during addon updates

## [0.30.2] - 2026-02-04

### Improvements
- **Detailed machine state detection** — Machine state now reflects actual extraction stages and phases (e.g., "Pre Infusion", "Ramp", "Hold", "Decline", etc.) for visibility into exactly what your machine is doing, not just Idle/Brewing

### Fixes
- **Preheat countdown sensor** — Now displays with whole-second precision (e.g., "45s" instead of "45.63s") and uses proper timer icon in Home Assistant
- **Preheat countdown reset** — Countdown timer properly resets to 0 when preheating finishes, preventing stale countdown values in Home Assistant

## [0.30.1] - 2026-01-31

### Fixes
- **State capitalization** — Machine state is now always published with consistent capital casing (Idle, Heating, Preheating, etc. instead of idle, heating, preheating)
- **State publication during preheat** — Machine state now updates in Home Assistant when preheating begins or ends, not just the preheat countdown timer

## [0.30.0] - 2026-01-31

### New Features
- **Expanded machine states** — Machine now reports detailed states (Preheating, Heating, Purging, Retracting, Closing Valve, Booting, Starting) instead of just Idle/Brewing
- **Preheat countdown timer** — New `preheat_remaining` sensor shows preheating progress in seconds
- **Real-time status detection** — Detects preheating, heating cycles, purging operations, and other machine phases for better visibility into what your machine is doing

### Improvements
- Better Home Assistant state entity descriptions reflecting new states

## [0.29.2] - 2026-01-31

### Fixes
- Clean up stale `select_profile` entity from Home Assistant that was removed in v0.29.1

## [0.29.1] - 2026-01-31

### Fixes
- Removed redundant `select_profile` button (the `active_profile` dropdown already provides profile selection)

## [0.29.0] - 2026-01-31

### New Features
- **`run_profile` command** — Load and preheat a profile in one action (complements `select_profile` which just highlights without loading)

### Improvements
- **Entity descriptions** — Added descriptions to all sensors and commands for better documentation and future integration enhancements
- **Sensor icons** — Updated icons throughout Home Assistant for better visual representation of sensor data (flow rate, weight, shot information, profiles, and more)
- **Profile command semantics** — Renamed `load_profile` to `select_profile` for clarity: select highlights the profile on the machine (you must press the button to load), while the new `run_profile` command actually loads and preheats it

## [0.28.3] - 2026-01-31

### Fixes
- **Containerized Home Assistant support** — Fixed MQTT integration for containerized Home Assistant installs without supervisor. The add-on now properly publishes entities when MQTT credentials are manually configured.

## [0.28.2] - 2026-01-29

### Improvements
- **Entity descriptions** — Added helpful descriptions to all sensors and commands displayed in Home Assistant UI

## [0.28.1] - 2026-01-29

### Fixes
- **Auto-cleanup on version upgrade** — Old MQTT entities are automatically removed when upgrading from earlier versions. No manual deletion of devices needed.

## [0.28.0] - 2026-01-27

### Breaking Changes
⚠️ **Command names updated for clarity** - Commands now use "shot" terminology consistently:
- `start_brew` → `start_shot` — Start a shot (load & execute profile)
- `stop_brew` → `stop_shot` — Stop the plunger immediately mid-shot
- `continue_brew` → `continue_shot` — Resume a paused shot

If you have Home Assistant automations using these commands, update them to use the new names.

### New Features
- **`abort_shot`** — Abort the current profile and retract the plunger (new action)
- **`home_plunger`** — Reset the plunger to home position (new action)
- **`purge`** — Flush water through the group head (new action)
- **Command descriptions** — All commands now display descriptions in Home Assistant's "More Info" UI to help you understand what each control does

## [0.27.1] - 2026-01-26

### Fixes
- **Brightness control cleaned up** - Removed complex Socket.IO state reading that wasn't working. Brightness now uses simple MQTT command and state model - when you adjust the slider, the add-on sends the command to the machine and publishes the result
- **Startup brightness initialization restored** - Sets brightness to 50% when the add-on starts to align the Home Assistant slider with the machine's actual state

## [0.27.0] - 2026-01-26

### Fixes
- **Fixed brightness 1-step lag with double-send workaround** - Device has a command processing queue that causes brightness changes to appear one step behind. Workaround: send brightness commands twice to the API so the device queue returns the correct value on the first event
- **Fixed brightness resetting to 50% unexpectedly** - Brightness initialization now only happens once when the add-on starts, not every time MQTT reconnects
- **Improved delta filtering** - First brightness update now passes through delta filter correctly to set the baseline, preventing the first update from being blocked

## [0.26.13] - 2026-01-26

### Fixes
- **Fixed brightness oscillation issue** - Device returns brightness as 0-1 (decimal), now converting to 0-100 for Home Assistant. Also filters small changes (less than 1%) to stop oscillation from rounding between 49-50

## [0.26.12] - 2026-01-26

### Fixes
- **Fixed brightness 1-step lag (found the right data)** - Device doesn't send brightness in settings change events. It's actually included in temperature sensor events (the a_0 field). Updated to read brightness from the right place

## [0.26.11] - 2026-01-26

### Fixes
- Device command queue causes brightness to appear one step behind. Publishing immediately from the command handler doesn't work because the device hasn't processed it yet. Now brightness only publishes from Socket.IO when device confirms the change

## [0.26.10] - 2026-01-26

### Fixes
- Brightness changes now publish with `retain=True` to overwrite stale retained messages on the broker, so Home Assistant always gets the current value

## [0.26.9] - 2026-01-26

### Improvements
- Reduced excessive Socket.IO event logging. Was logging hundreds of packets per second making logs unreadable. Now only meaningful changes logged

## [0.26.8] - 2026-01-26

### Fixes
- Fixed brightness feedback loop where retained messages were overwriting immediate command publishing
- Brightness initializes to 50% on startup to sync the Home Assistant slider with the machine

## [0.26.7] - 2026-01-26

### Fixes
- Fixed brightness state publishing to avoid feedback loops with stale retained messages

## [0.26.6] - 2026-01-26

### Fixes
- Fixed brightness command lag caused by immediate state publishing creating MQTT feedback loops

## [0.26.5] - 2026-01-26

### Fixes
- Pinned pymeticulous to version 0.3.1 to avoid installation issues with version 0.3.0 that had validation bugs

## [0.26.4] - 2026-01-26

### Fixes
- Action handlers now properly check response status to catch when the machine rejects actions (like trying to tare while extracting)
- Fixed brightness value conversion to use the correct float type for API validation

## [0.26.3] - 2026-01-26

### Fixes
- Machine actions now work properly (start brew, stop, preheat, tare, etc.)
- Profile selection now responds correctly to your choices
- Updated to pyMeticulous 0.3.1 with bug fixes

## [0.26.2] - 2026-01-20

### Improvements
- Add-on now clears stale Home Assistant entities on startup, so you don't have old orphaned entities
- Reduced log verbosity by moving diagnostic details to debug level

## [0.26.1] - 2026-01-20

### Improvements
- Improved logging to help diagnose sensor issues
- Fixed connection timing during startup

## [0.26.0] - 2026-01-20

### Fixes
- All sensors now display properly instead of showing "unknown"
- Brightness control no longer appears as a duplicate sensor
- Sounds toggle now appears correctly in Home Assistant
- Profile selector shows your currently selected profile
- All sensor values load immediately when the add-on starts
- Updated to pyMeticulous 0.3.1 for better machine communication

## [0.5.25] - 2026-01-20

### Improvements
- Added better diagnostics to help troubleshoot sensor visibility issues

## [0.5.24] - 2026-01-20

### Improvements
- Updated core machine communication for better reliability

## [0.5.23] - 2026-01-17

### Fixes
- Profile selector now shows your current choice
- All machine values load immediately when the add-on starts
- Sounds and brightness controls now appear correctly in Home Assistant

## [0.5.22] - 2026-01-17

### Fixes
- Sensors no longer show "unknown" when they should show real values
- All machine information loads properly at startup

## [0.5.21] - 2026-01-17

### Performance
- Reduced unnecessary sensor messages so your network stays quieter while sensors still update responsively
- New settings let you control how often sensors refresh

## [0.5.20] - 2026-01-15

### Improvements
- Fixed how your machine appears as a device in Home Assistant

## [0.5.19] - 2026-01-15

### Improvements
- Fixed how Home Assistant recognizes the add-on

## [0.5.18] - 2026-01-15

### Improvements
- Improved connection handshake with Home Assistant

## [0.5.17] - 2026-01-15

### Performance
- Sensors now appear in Home Assistant much faster after startup

## [0.5.16] - 2026-01-15

### Fixes
- Fixed device name consistency in Home Assistant

## [0.5.15] - 2026-01-15

### Improvements
- Better diagnostic information for troubleshooting connection issues

## [0.5.14] - 2026-01-15

### Improvements
- Improved sensor discovery reliability

## [0.5.13] - 2026-01-15

### Improvements
- Better error handling for sensor discovery

## [0.5.12] - 2026-01-15

### Fixes
- Fixed sensors not appearing in Home Assistant after starting the add-on

## [0.5.11] - 2026-01-15

### Improvements
- Better diagnostics for connection troubleshooting

## [0.5.10] - 2026-01-15

### Fixes
- Fixed sensors not appearing after startup

## [0.5.9] - 2026-01-15

### Improvements
- Added troubleshooting information for sensor discovery

## [0.5.8] - 2026-01-15

### Fixes
- Fixed sensors disappearing after add-on restart - they now reappear properly in Home Assistant

## [0.5.7] - 2026-01-15

### Fixes
- Fixed sensors not reaching Home Assistant

## [0.5.6] - 2026-01-15

### Fixes
- Improved message delivery to Home Assistant

## [0.5.5] - 2026-01-15

### Fixes
- Improved connection reliability

## [0.5.4] - 2026-01-14

### New Features
- New commands: `continue_brew` and `reboot_machine`
- Firmware update sensor so you know when updates are available for your machine
- Brightness is now a slider for easier adjustment
- Configurable refresh rate for sensor updates (1-60 minutes, default 5)

### Fixes
- Fixed profile loading reliability
- Improved command execution

## [0.5.1-0.5.3] - 2026-01-09

### Fixes
- Fixed profile selector dropdown on startup
- Improved profile selection reliability

## [0.5.0] - 2026-01-09

### New Features
Your Meticulous machine is now fully controllable from Home Assistant!
- Start, stop, and continue brewing
- Preheat your machine and tare the scale with buttons
- Adjust brightness with a slider and toggle sounds on/off
- Switch between profiles with a dropdown menu
- All sensors update instantly when you interact with your machine

## [0.4.0-0.4.3] - 2026-01-09

### Features
All sensors now update instantly when you interact with your machine - no more waiting for polling updates!

### Fixes
- Fixed crashes during live updates
- Improved profile loading with fractional timestamps

## [0.3.0-0.3.6] - 2026-01-09

### Features
- Full Home Assistant integration - your Meticulous machine appears with sensors and controls
- Real-time updates for machine status, temperature, pressure, and timing
- Create automations based on your machine's state
- All sensors appear immediately in Home Assistant on startup

## [0.1.0] - 2026-01-07

- Initial release with MQTT discovery and Meticulous Espresso integration
