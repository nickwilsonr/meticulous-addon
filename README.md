# Meticulous Espresso Home Assistant Add-on

Integrate your Meticulous Espresso machine with Home Assistant for real-time monitoring, automation, and control.

## Features

- **Real-time brewing data**: Pressure, flow rate, weight, shot timer
- **Temperature monitoring**: Boiler and brew head temperatures
- **22+ automatic sensors**: Machine status, profiles, statistics, device info
- **8 control commands**: Start/stop brew, preheat, tare scale, load profiles, adjust brightness/sounds
- **MQTT auto-discovery**: Entities appear automatically in Home Assistant
- **Graceful reconnection**: Automatic recovery from network issues

---

## Installation

### Via Home Assistant

1. **Add this repository** to Home Assistant:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the **⋮** menu → **Repositories**
   - Add: `https://github.com/nickwilsonr/meticulous-addon`

2. **Install the add-on:**
   - Find "Meticulous Espresso" in the store
   - Click **INSTALL**

3. **Configure:**
   - Go to the **Configuration** tab
   - Set `machine_ip` to your Meticulous machine's IP address (e.g., `192.168.1.100`)
   - Adjust other settings if needed (see [Configuration](#configuration) below)

4. **Start:**
   - Click **SAVE** then **START**
   - Check the **Log** tab to verify connection

---

## Configuration

### Required Settings

**`machine_ip`** (required)
The IP address or hostname of your Meticulous machine on your local network.

Example:
```yaml
machine_ip: "192.168.1.100"
# or
machine_ip: "meticulous.local"
```

### Optional Settings

**`scan_interval`** (default: 30)
How often (in seconds) to poll for statistics and device info. Range: 10-300.

**`debug`** (default: false)
Enable debug logging for detailed troubleshooting.

### MQTT Settings

**`mqtt_enabled`** (default: true)
Enable MQTT discovery (requires MQTT broker like Mosquitto).

**`mqtt_host`** (default: "core-mosquitto")
MQTT broker hostname.

**`mqtt_port`** (default: 1883)
MQTT broker port.

**`mqtt_username`** / **`mqtt_password`** (optional)
MQTT credentials if required by your broker. These are automatically fetched from the Home Assistant MQTT integration when available, so you typically don't need to configure them manually.

---

## Available Entities

Once connected, the add-on automatically creates entities in Home Assistant:

### Sensors

- **Status**: `sensor.meticulous_state`, `binary_sensor.meticulous_brewing`
- **Temperature**: `sensor.meticulous_boiler_temperature`, `sensor.meticulous_brew_head_temperature`
- **Brewing**: `sensor.meticulous_shot_timer`, `sensor.meticulous_pressure`, `sensor.meticulous_flow_rate`, `sensor.meticulous_shot_weight`
- **Profile**: `sensor.meticulous_active_profile`, `sensor.meticulous_profile_author`
- **Statistics**: `sensor.meticulous_total_shots`, `sensor.meticulous_last_shot_name`, `sensor.meticulous_last_shot_rating`
- **Settings**: `sensor.meticulous_brightness`, `binary_sensor.meticulous_sounds_enabled`
- **Device**: `sensor.meticulous_firmware_version`, `sensor.meticulous_software_version`, `sensor.meticulous_voltage`

### Commands (via MQTT)

Publish to these topics to control your machine:

- `meticulous_espresso/command/start_brew` — Start brewing
- `meticulous_espresso/command/stop_brew` — Stop brewing
- `meticulous_espresso/command/preheat` — Preheat machine
- `meticulous_espresso/command/tare_scale` — Tare the scale
- `meticulous_espresso/command/load_profile` — Load profile (payload: `profile_id`)
- `meticulous_espresso/command/set_brightness` — Set brightness (payload: 0-100)
- `meticulous_espresso/command/enable_sounds` — Enable/disable sounds (payload: `true`/`false`)

---

## Example Automation

**Shot Complete Notification:**
```yaml
automation:
  - alias: "Espresso Shot Complete"
    trigger:
      - platform: state
        entity_id: binary_sensor.meticulous_brewing
        from: "on"
        to: "off"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Your espresso is ready! {{ states('sensor.meticulous_shot_weight') }}g in {{ states('sensor.meticulous_shot_timer') }}s"
```

For more examples, see [docs/automations.md](docs/automations.md).

---

## Troubleshooting

**Add-on won't start:**
- Check the **Log** tab for errors
- Verify `machine_ip` is correct
- Ensure your machine is on and connected to the network
- Check that port 8080 is accessible

**Sensors not updating:**
- Verify the add-on is connected (check logs for Socket.IO connection)
- Ensure MQTT broker (Mosquitto) is running
- Try restarting the add-on

**Connection keeps dropping:**
- Check network stability between Home Assistant and machine
- Verify machine firmware is up to date

**Entities not appearing:**
- Ensure `mqtt_enabled` is `true`
- Check MQTT broker is configured correctly
- Verify MQTT integration is set up in Home Assistant
- Check logs for MQTT connection errors

---

## Documentation

- [Automations Guide](docs/automations.md) — Example automations for Meticulous
- [MQTT Topics Reference](docs/mqtt-topics.md) — Complete command reference

**For Developers:**
- [Development Guide](docs/development.md) — Setup and architecture details
- [Contributing Guide](docs/CONTRIBUTING.md) — How to contribute code or report technical issues

---

## Support

**Issues & Feature Requests:**
https://github.com/nickwilsonr/meticulous-addon/issues

**Developer Info:**
See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) if you want to contribute code or report technical issues.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
