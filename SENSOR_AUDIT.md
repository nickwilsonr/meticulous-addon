# Sensor Type Audit

## Floating Point Sensors (Numeric - need delta-based throttling)
These represent measurements that can vary continuously and should use delta thresholds:

1. **boiler_temperature** - float (°C) - Very chatty, high frequency updates
2. **brew_head_temperature** - float (°C) - Very chatty, high frequency updates
3. **external_temp_1** - float (°C) - May be chatty if sensor present
4. **external_temp_2** - float (°C) - May be chatty if sensor present
5. **pressure** - float (bar) - Very chatty during extraction, high frequency
6. **flow_rate** - float (ml/s) - Very chatty during extraction, high frequency
7. **shot_weight** - float (g) - Chatty during extraction, updates as weight increases
8. **shot_timer** - float (seconds) - Very chatty, increments every frame (~100Hz)
9. **elapsed_time** - float (seconds) - Very chatty, increments every frame (~100Hz)
10. **target_temperature** - float (°C) - Rarely changes, low priority for delta
11. **target_weight** - float (g) - Rarely changes, low priority for delta
12. **target_pressure** - float (bar) - Rarely changes (if included), low priority
13. **target_flow** - float (ml/s) - Rarely changes (if included), low priority
14. **voltage** - float (V) - Rarely changes, low priority for delta
15. **brightness** - float (0-100 or 0-1) - User-controlled, should publish on change

## String/Text Sensors (need change detection)
These represent categorical/text data that changes infrequently:

1. **state** - string (e.g., "idle", "heating", "extracting") - Should publish on change
2. **active_profile** - string (profile name) - Should publish on change
3. **last_shot_name** - string - Should publish on change (new shot)
4. **last_shot_profile** - string - Should publish on change (new shot)
5. **last_shot_rating** - string (e.g., "good", "ok", "bad") - Should publish on change
6. **profile_author** - string - Should publish on change
7. **firmware_version** - string - Should publish on change (rarely)
8. **software_version** - string - Should publish on change (rarely)

## Boolean/Binary Sensors (need change detection)
These represent on/off states:

1. **connected** - boolean - Should publish on change
2. **brewing** - boolean - Should publish on change
3. **sounds_enabled** - boolean - Should publish on change
4. **firmware_update_available** - boolean - Should publish on change

## Timestamp Sensors (need change detection)
These represent point-in-time data:

1. **last_shot_time** - ISO timestamp - Should publish on change (new shot)

## Integer Sensors (need delta-based throttling)
These represent counts:

1. **total_shots** - integer - Should publish on change (new shot)

## Summary by Sensor Category

### High-Frequency Chatty Sensors (need aggressive delta thresholds)
- Temperature: 0.1-1.0°C delta
- Pressure: 0.1-0.5 bar delta
- Flow Rate: 0.1-0.5 ml/s delta
- Weight: 0.1-0.5g delta
- Timers (shot_timer, elapsed_time): 0.5-1.0s delta (or every Nth update)

### Medium-Frequency Sensors (moderate delta)
- Voltage: 1.0V delta
- Target values: any change (rarely updates)

### Low-Frequency State Changes (exact match / change detection)
- State, Profile, Brewing, Connected: publish on any change
- Shot info: publish on any change
- Settings (sounds, brightness): publish on any change

## Recommended Delta Thresholds

```python
SENSOR_DELTA_THRESHOLDS = {
    # Temperatures - 0.5°C threshold
    "boiler_temperature": 0.5,
    "brew_head_temperature": 0.5,
    "external_temp_1": 0.5,
    "external_temp_2": 0.5,

    # Pressure - 0.2 bar threshold
    "pressure": 0.2,

    # Flow - 0.1 ml/s threshold
    "flow_rate": 0.1,

    # Weight - 0.1g threshold
    "shot_weight": 0.1,

    # Timers - 1.0s threshold
    "shot_timer": 1.0,
    "elapsed_time": 1.0,

    # Targets - always publish (rarely change)
    "target_temperature": 0.0,  # 0 = any change
    "target_weight": 0.0,
    "target_pressure": 0.0,
    "target_flow": 0.0,

    # Voltage - 1.0V threshold
    "voltage": 1.0,

    # Brightness - 1 point threshold
    "brightness": 1,
}

# String/Boolean/Timestamp sensors - always publish on change
EXACT_MATCH_SENSORS = {
    "state", "active_profile", "brewing", "connected",
    "last_shot_name", "last_shot_profile", "last_shot_rating",
    "profile_author", "firmware_version", "software_version",
    "last_shot_time", "firmware_update_available", "sounds_enabled",
    "total_shots"  # Integer but rare changes
}
```
