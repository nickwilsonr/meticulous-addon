# Developer Guide

**For:** Contributors and developers
**Audience:** Anyone building, testing, or extending the add-on

---

## Quick Start

1. **Clone and install:**
   ```bash
   git clone https://github.com/nickwilsonr/meticulous-addon.git
   cd meticulous-addon
   pip install -r requirements.txt
   ```

2. **Set up pre-commit hooks (required):**
   ```bash
   pip install pre-commit
   pre-commit install
   ```
   This ensures code quality checks run automatically before each commit. Required to push to this repository.

3. **Configure:**
   Create `/data/options.json`:
   ```json
   {
     "machine_ip": "192.168.1.100",
     "scan_interval": 30,
     "debug": true
   }
   ```

4. **Run:**
   ```bash
   python rootfs/usr/bin/run.py
   ```

---

## Project Structure

```
meticulous-addon/
├── .github/workflows/builder.yml      # CI/CD for multi-arch builds
├── rootfs/usr/bin/run.py              # Main app (688 lines)
├── translations/en.json               # UI descriptions
├── config.json                        # Add-on config schema
├── Dockerfile                         # Container build
├── requirements.txt                   # Python dependencies
├── .pre-commit-config.yaml            # Code quality hooks
└── docs/                              # Documentation
```

---

## Code Quality & Pre-Commit Hooks

This project uses **pre-commit** to enforce code quality standards automatically:

**What gets checked:**
- **Black**: Code formatting (Python)
- **Flake8**: Linting and style compliance
- **isort**: Import statement organization
- **Trailing whitespace**: Removes extra spaces
- **End-of-file fixer**: Ensures proper file endings
- **YAML validation**: Checks workflow and config syntax
- **JSON validation**: Checks data file syntax

**What to do:**
1. After cloning, run: `pre-commit install`
2. Hooks will run automatically before each commit
3. If checks fail, fix the issues and try committing again
4. To run checks manually: `pre-commit run --all-files`

**Note:** Commits that fail pre-commit checks cannot be pushed to master due to branch protection rules.

---

## Dependency: pyMeticulous

**Status:** Requires v0.2.0+ with Socket.IO (now available on PyPI)

### Installation

```bash
pip install pymeticulous>=0.2.0
```

### What v0.2.0 Includes

- Socket.IO support for real-time events
- Event handlers: `onStatus`, `onTemperatureSensors`, `onProfileChange`, `onNotification`
- Updated v0.2.0 API surface

### Resources

Package: https://pypi.org/project/pyMeticulous/

---

## Architecture Overview

### Real-Time (Socket.IO)
- **onStatus**: State, brewing sensors (pressure, flow, weight)
- **onTemperatureSensors**: Boiler and brew head temps
- **onProfileChange**: Profile loaded/changed
- **onNotification**: Machine alerts

### Polling (Periodic)
- Profile info (on change events)
- Statistics (5-10 min)
- Device info (30 min)

### Data Flow
```
Machine API → Socket.IO + REST → Add-on → MQTT → Home Assistant
```

### Key Functions (run.py)
- `_handle_status_event()`: Real-time brewing data
- `_handle_temperature_event()`: Temperature updates
- `maintain_socket_connection()`: Auto-reconnect with backoff
- `periodic_updates()`: Polling loop

---

## Configuration

**Add-on Options (config.yaml):**
```json
{
  "machine_ip": "192.168.1.100",              // IP or hostname (required)
  "enable_delta_filtering": true,             // Filter small sensor changes
  "temperature_delta": 0.5,                   // °C threshold
  "pressure_delta": 0.2,                      // bar threshold
  "flow_delta": 0.1,                          // ml/s threshold
  "weight_delta": 0.1,                        // g threshold
  "time_delta": 0.1,                          // s threshold
  "voltage_delta": 1.0,                       // V threshold
  "stale_data_refresh_interval": 24,          // hours (1-168)
  "debug": false,                             // Enable debug logging
  "mqtt_enabled": true,                       // Enable MQTT discovery
  "mqtt_host": "core-mosquitto",              // MQTT broker
  "mqtt_port": 1883,                          // MQTT port
  "mqtt_username": "",                        // Auto-fetched from HA
  "mqtt_password": ""                         // Auto-fetched from HA
}
```

**Note:** MQTT credentials are automatically retrieved from the Home Assistant Supervisor Services API when the MQTT integration is configured, so you typically don't need to set `mqtt_username` or `mqtt_password` manually.

---

## Testing

The add-on includes a comprehensive test suite with 27 passing tests covering core functionality:

### Running Tests

```bash
# From the root directory
python tests/run_tests.py

# Or with verbose output
python -m unittest discover tests -v
```

### Test Coverage

**test_mqtt_commands.py** (18 tests):
- All MQTT command handlers (start_brew, stop_brew, continue_brew, preheat, tare_scale)
- Load profile with validation
- Set brightness (integer and JSON payloads)
- Enable/disable sounds (multiple payload formats)
- Error handling with missing API
- MQTT message routing and exception handling

**test_addon_integration.py** (14 tests):
- Configuration loading from options.json
- Default configuration values
- Retry logic and exponential backoff
- State management and availability
- Health metrics tracking
- Import validation (pyMeticulous, paho-mqtt)

### Writing New Tests

When adding features:
1. Add unit tests in `tests/test_mqtt_commands.py` for command handlers
2. Add integration tests in `tests/test_addon_integration.py` for system behavior
3. Mock external dependencies (API, MQTT) to isolate functionality
4. Run tests before committing changes

See [tests/README.md](../tests/README.md) for more details.

---

## Testing Checklist

- [ ] Socket.IO connected to machine
- [ ] Real-time brewing sensors update
- [ ] Temperature sensors update
- [ ] Auto-reconnect works after disconnect
- [ ] MQTT entities created automatically
- [ ] Services work (start, stop, tare, load_profile, etc.)
- [ ] Error handling graceful
- [ ] Logs show expected events

---

## Roadmap

**Phase 1 (MVP - Current):**
- Socket.IO connection with auto-reconnect
- 24 core sensors (status, temps, brewing, profile, stats, device, connectivity)
- 8 commands (brew, preheat, tare, profile load, brightness, sounds)
- MQTT discovery with delta filtering

**Phase 2 (Enhanced):**
- Profile listing and selection UI
- Shot history visualization
- Advanced automations examples
- Settings UI improvements

**Phase 3 (Advanced):**
- Predictive preheat based on schedule
- Shot trend analysis
- Recipe app integration
- Voice assistant examples
- Maintenance tracking

**Phase 4 (Release):**
- Complete documentation
- HACS publication
- Community feedback integration

---

## Contributing

1. Conventional commits
2. PEP 8 style, type hints, docstrings
3. Add tests for new features
4. Update CHANGELOG
5. Submit PR with clear description

---

## Release Process

1. Update CHANGELOG and version in config.json
2. Tag and push to GitHub
3. GitHub Actions builds and publishes multi-arch images

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Won't start | Check logs, verify machine IP and network |
| Socket.IO fails | Verify port 8080 is open |
| Sensors not updating | Check connection, restart add-on |
| MQTT not working | Verify broker running and credentials |

---

## Resources

- [HA Add-on Development](https://developers.home-assistant.io/docs/add-ons)
- [pyMeticulous](https://github.com/MeticulousHome/pyMeticulous)
- [Meticulous API](https://github.com/MeticulousHome/meticulous-typescript-api)

---

## See Also

- [Architecture & Integration Details](architecture.md)
- [Automations Examples](automations.md)
- [MQTT Topics Reference](mqtt-topics.md)
- [How to Contribute](CONTRIBUTING.md)
