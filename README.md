# Meticulous Espresso Home Assistant Add-on

Integrate your Meticulous Espresso machine with Home Assistant for real-time monitoring, automation, and control.

## Features

- **Real-time brewing data**: Pressure, flow rate, weight, shot timer
- **Temperature monitoring**: Boiler and brew head temperatures
- **25 automatic sensors**: Machine status, profiles, statistics, device info, connectivity
- **8 control commands**: Start/stop/continue brew, preheat, tare scale, load profiles, adjust brightness, toggle sounds
- **Profile image entity**: Active profile image available as a native HA image entity for use in dashboards
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

**`enable_delta_filtering`** (default: true)
Reduce MQTT message volume by filtering small sensor changes. Helps with network efficiency while keeping updates responsive. When enabled, small fluctuations in temperature, pressure, flow, weight, and time are filtered out.

**`temperature_delta`** (default: 0.5°C)
**`pressure_delta`** (default: 0.2 bar)
**`flow_delta`** (default: 0.1 ml/s)
**`weight_delta`** (default: 0.1 g)
**`time_delta`** (default: 0.1 s)
**`voltage_delta`** (default: 1.0 V)
Minimum change thresholds for each sensor type before publishing an update. Increase these values to reduce message frequency (may delay updates), or decrease to catch smaller changes.

**`stale_data_refresh_interval`** (default: 24 hours, range: 1-168 hours)
How often to do a full refresh of all sensor states from the machine, ensuring data stays current even if Socket.IO events are missed. This is a safety mechanism to keep your data accurate.

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

### Sensors (25 total)

**Connectivity & Status** (3 sensors)
- `binary_sensor.meticulous_connected` — Machine connection status
- `sensor.meticulous_state` — Current machine state (idle, brewing, steaming, heating, error)
- `binary_sensor.meticulous_brewing` — Is machine actively extracting?

**Temperature** (5 sensors)
- `sensor.meticulous_boiler_temperature` — Boiler temperature
- `sensor.meticulous_brew_head_temperature` — Brew head temperature
- `sensor.meticulous_external_temp_1` — External sensor 1
- `sensor.meticulous_external_temp_2` — External sensor 2
- `sensor.meticulous_target_temperature` — Profile target temperature

**Brewing Data** (6 sensors)
- `sensor.meticulous_shot_timer` — Elapsed time (seconds)
- `sensor.meticulous_pressure` — Current pressure (bar)
- `sensor.meticulous_flow_rate` — Current flow (ml/s)
- `sensor.meticulous_shot_weight` — Current weight (grams)
- `sensor.meticulous_target_weight` — Profile target weight

**Profile** (4 sensors)
- `sensor.meticulous_active_profile` — Currently loaded profile name
- `sensor.meticulous_profile_author` — Profile creator
- `image.meticulous_active_profile_image` — Active profile image
- `sensor.meticulous_active_profile_filename` — Active profile image filename (useful for cache-busting in dashboard templates)

**Statistics** (4 sensors)
- `sensor.meticulous_total_shots` — Lifetime shot count
- `sensor.meticulous_last_shot_name` — Last shot name
- `sensor.meticulous_last_shot_rating` — Last shot rating (👍/👎/unmarked)
- `sensor.meticulous_last_shot_time` — Timestamp of last shot

**Device Info** (3 sensors)
- `sensor.meticulous_firmware_version` — Machine firmware version
- `sensor.meticulous_software_version` — Machine software version
- `sensor.meticulous_voltage` — Power supply voltage

**Settings** (2 sensors)
- `switch.meticulous_sounds_enabled` — Sound on/off toggle
- `sensor.meticulous_brightness` — Display brightness (0-100)

### Controls

- **Brightness (slider)**: `number.meticulous_brightness` — Adjust display brightness (0-100)
- **Sounds (switch)**: `switch.meticulous_sounds_enabled` — Toggle sounds on/off
- **Active Profile (select)**: `select.meticulous_active_profile` — Switch between available profiles

### Commands (11 total)

These are available as buttons/switches in Home Assistant:

- `start_shot` — Start a shot (load & execute profile)
- `stop_shot` — Stop the plunger immediately mid-shot
- `continue_shot` — Resume a paused shot
- `abort_shot` — Abort the current profile and retract plunger
- `preheat` — Preheat water in chamber to target temperature
- `tare_scale` — Zero the scale
- `home_plunger` — Reset plunger to home position
- `purge` — Flush water through group head
- `load_profile` — Switch to a different profile
- `set_brightness` — Adjust display brightness with a slider (0-100)
- `enable_sounds` — Toggle sound effects on/off

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
