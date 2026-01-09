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

2. **Configure:**
   Create `/data/options.json`:
   ```json
   {
     "machine_ip": "192.168.1.100",
     "scan_interval": 30,
     "log_level": "debug"
   }
   ```

3. **Run:**
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
└── docs/                              # Documentation
```

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

**Add-on Options (config.json):**
```json
{
  "machine_ip": "192.168.1.100",  // IP or hostname
  "scan_interval": 30,             // 10-300 seconds
  "log_level": "info",             // debug/info/warning/error
  "retry_initial": 2,              // Initial retry delay (seconds)
  "retry_max": 60,                 // Max retry delay (seconds)
  "retry_jitter": true,            // Add 0-20% randomness
  "mqtt_enabled": true,            // Enable MQTT discovery
  "mqtt_host": "core-mosquitto",   // MQTT broker
  "mqtt_port": 1883
}
```

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
- 22 core sensors (status, temps, brewing, profile, stats, device)
- 8 basic commands (brew, preheat, tare, brightness, sounds)
- MQTT discovery

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
