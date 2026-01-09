## [0.2.2] - 2026-01-08

### Fixed
- Release workflow visibility step now uses GitHub REST API via `curl` to set GHCR packages public.
- Limited builds to `amd64` and `aarch64` to match Supervisor-supported platforms.

### Changed
- Add-on manifest `arch` updated to only `aarch64` and `amd64`.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-08
## [0.2.1] - 2026-01-08

### Fixed
- Unit tests pass consistently; safe async scheduling wrapper prevents event loop errors in tests.
- Resolved Pylance issues by fixing multi-line f-strings and reducing long lines.

### Added
- Helper wrappers for MQTT discovery payloads and backoff calculation to align with tests.
- CI lint workflow (flake8) to enforce style.

### Changed
- VS Code / Pyright configuration to improve import resolution in non-standard layout.


### Changed
- Updated to use pyMeticulous 0.2.0 from PyPI (previously from git branch)
- Removed dependency on unreleased PR branch
- Updated documentation to reflect pyMeticulous availability

### Added
- Comprehensive test suite for addon functionality

## [0.1.0] - 2026-01-07

### Added
- Initial release
- Real-time monitoring via Socket.IO event streaming
- 22+ sensors for machine status, temperature, pressure, brewing metrics, profiles, and statistics
- MQTT discovery for automatic entity creation in Home Assistant
- MQTT-based command interface (start_brew, stop_brew, continue_brew, preheat, tare_scale, load_profile, set_brightness, enable_sounds)
- Exponential backoff with jitter for resilient reconnections
- Health metrics publishing (uptime, reconnect count, error tracking)
- Graceful degradation during network outages with availability tracking
- Configurable retry behavior (initial delay, max delay, jitter)
- Support for external MQTT brokers or Home Assistant Mosquitto add-on
- Comprehensive event handlers for status, temperature, profile, and notification events
- Polling for non-real-time data (profiles, settings, statistics)
- Device registry integration with firmware/software version tracking
- Multi-arch Docker support (armhf, armv7, aarch64, amd64, i386)
