# Example Automations for Meticulous Espresso Integration

This file contains practical automation examples for Home Assistant users with a Meticulous Espresso machine.

## Table of Contents
- [Shot Preparation](#shot-preparation)
- [Shot Notifications](#shot-notifications)
- [Profile Management](#profile-management)
- [Smart Controls](#smart-controls)
- [Shot Tracking & Analysis](#shot-tracking--analysis)
- [Voice Control](#voice-control)
- [Advanced Automations](#advanced-automations)

---

## Shot Preparation

### On-Demand Profile Loading

Load your preferred profile when you're ready to make coffee.

```yaml
input_select:
	current_coffee_bean:
		name: "Current Coffee Beans"
		options:
			- "Ethiopia Light Roast"
			- "Colombia Medium Roast"
			- "Italian Dark Roast"
		initial: "Ethiopia Light Roast"

automation:
	- id: load_bean_profile
		alias: "Meticulous: Load Bean Profile"
		description: "Load the matching profile when beans change"
		trigger:
			- platform: state
				entity_id: input_select.current_coffee_bean
		action:
			- choose:
					- conditions:
							- condition: state
								entity_id: input_select.current_coffee_bean
								state: "Ethiopia Light Roast"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "ethiopia-profile-id"
					- conditions:
							- condition: state
								entity_id: input_select.current_coffee_bean
								state: "Colombia Medium Roast"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "colombia-profile-id"
					- conditions:
							- condition: state
								entity_id: input_select.current_coffee_bean
								state: "Italian Dark Roast"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "italian-profile-id"
			- service: notify.mobile_app_phone
				data:
					message: "Profile loaded: {{ states('sensor.meticulous_active_profile') }}"
```

### Quick Brew Button

One-button workflow to start brewing.

```yaml
script:
	meticulous_quick_brew:
		alias: "Meticulous: Quick Brew"
		sequence:
			- service: meticulous.start_brew
			- service: notify.mobile_app_phone
				data:
					message: "☕ Brewing started!"
```

Add to Lovelace dashboard:
```yaml
type: button
name: Brew Shot
icon: mdi:coffee
tap_action:
	action: call-service
	service: script.meticulous_quick_brew
```

### Chamber Water Reminder

Remind yourself to add fresh water to the chamber before pulling a shot (since the Meticulous doesn't have a reservoir).

```yaml
input_boolean:
	meticulous_water_added:
		name: "Water Added to Chamber"
		icon: mdi:water

automation:
	- id: meticulous_water_reminder
		alias: "Meticulous: Water Chamber Reminder"
		description: "Remind to add water before brewing"
		trigger:
			- platform: state
				entity_id: binary_sensor.meticulous_brewing
				to: "on"
		condition:
			- condition: state
				entity_id: input_boolean.meticulous_water_added
				state: "off"
		action:
			- service: notify.mobile_app_phone
				data:
					message: "💧 Did you add fresh water to the chamber?"
					data:
						ttl: 0
						priority: high

	- id: reset_water_reminder
		alias: "Meticulous: Reset Water Reminder"
		description: "Reset water flag after shot completes"
		trigger:
			- platform: state
				entity_id: binary_sensor.meticulous_brewing
				from: "on"
				to: "off"
		action:
			- delay: "00:01:00"  # Allow time for purge cycle
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.meticulous_water_added
```

---

## Shot Notifications

### Shot Complete Notification with Stats

Get detailed shot metrics when your espresso is ready.

```yaml
automation:
	- id: shot_complete
		alias: "Meticulous: Shot Complete"
		description: "Notify when shot finishes with stats"
		trigger:
			- platform: state
				entity_id: binary_sensor.meticulous_brewing
				from: "on"
				to: "off"
		action:
			- service: notify.mobile_app_phone
				data:
					title: "☕ Shot Complete!"
					message: >
						{{ states('sensor.meticulous_active_profile') }}
						{{ states('sensor.meticulous_shot_weight') }}g in {{ states('sensor.meticulous_shot_timer') }}s
						Max pressure: {{ states('sensor.meticulous_pressure') }} bar
					data:
						ttl: 0
						priority: high
						actions:
							- action: "RATE_GOOD"
								title: "👍 Good"
							- action: "RATE_BAD"
								title: "👎 Needs Work"
```

### Rate Shot from Notification

Rate your shot quality directly from the notification.

```yaml
automation:
	- id: rate_shot_good
		alias: "Meticulous: Rate Shot Good"
		trigger:
			- platform: event
				event_type: mobile_app_notification_action
				event_data:
					action: "RATE_GOOD"
		action:
			- service: meticulous.rate_last_shot
				data:
					rating: "like"
			- service: notify.mobile_app_phone
				data:
					message: "Shot rated 👍 - Great pull!"

	- id: rate_shot_bad
		alias: "Meticulous: Rate Shot Bad"
		trigger:
			- platform: event
				event_type: mobile_app_notification_action
				event_data:
					action: "RATE_BAD"
		action:
			- service: meticulous.rate_last_shot
				data:
					rating: "dislike"
			- service: notify.mobile_app_phone
				data:
					message: "Shot rated 👎 - Try adjusting grind or profile"
```

### Pressure Anomaly Alert

Get notified if pressure behavior is unusual during extraction.

```yaml
automation:
	- id: pressure_anomaly_alert
		alias: "Meticulous: Pressure Anomaly"
		description: "Alert if pressure drops or spikes unexpectedly"
		trigger:
			- platform: numeric_state
				entity_id: sensor.meticulous_pressure
				below: 5
				for:
					seconds: 3
		condition:
			- condition: state
				entity_id: binary_sensor.meticulous_brewing
				state: "on"
			- condition: numeric_state
				entity_id: sensor.meticulous_shot_timer
				above: 5
		action:
			- service: notify.mobile_app_phone
				data:
					message: "⚠️ Low pressure detected - check your puck prep or grind"
```

---

## Profile Management

### Profile Selector Dashboard

Quick profile switching from your dashboard.

```yaml
input_select:
	meticulous_profile:
		name: "Espresso Profile"
		options:
			- "Light Roast - High Temp"
			- "Medium Roast - Balanced"
			- "Dark Roast - Lower Temp"
			- "Experimental"
		initial: "Medium Roast - Balanced"

automation:
	- id: change_profile
		alias: "Meticulous: Change Profile"
		trigger:
			- platform: state
				entity_id: input_select.meticulous_profile
		action:
			- choose:
					- conditions:
							- condition: state
								entity_id: input_select.meticulous_profile
								state: "Light Roast - High Temp"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "light-roast-id"
					- conditions:
							- condition: state
								entity_id: input_select.meticulous_profile
								state: "Medium Roast - Balanced"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "medium-roast-id"
					- conditions:
							- condition: state
								entity_id: input_select.meticulous_profile
								state: "Dark Roast - Lower Temp"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "dark-roast-id"
					- conditions:
							- condition: state
								entity_id: input_select.meticulous_profile
								state: "Experimental"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "experimental-id"
			- service: notify.mobile_app_phone
				data:
					message: "Profile loaded: {{ trigger.to_state.state }}"
```

---

## Smart Controls

### Motion-Based Display Brightness

Automatically adjust display brightness based on presence detection.

```yaml
automation:
	- id: meticulous_motion_brighten
		alias: "Meticulous: Motion Detected - Brighten"
		description: "Brighten display when motion detected"
		trigger:
			- platform: state
				entity_id: binary_sensor.kitchen_motion
				to: "on"
		action:
			- service: meticulous.set_brightness
				data:
					brightness: 80
					animation_time: 500

	- id: meticulous_no_motion_dim
		alias: "Meticulous: No Motion - Dim"
		description: "Dim display after 5 minutes of no motion"
		trigger:
			- platform: state
				entity_id: binary_sensor.kitchen_motion
				to: "off"
				for:
					minutes: 5
		action:
			- service: meticulous.set_brightness
				data:
					brightness: 5
					animation_time: 1000
```

### Emergency Stop Button

Dashboard button to stop brewing immediately.

```yaml
script:
	meticulous_emergency_stop:
		alias: "Meticulous: Emergency Stop"
		sequence:
			- service: meticulous.stop_brew
			- service: notify.mobile_app_phone
				data:
					message: "⛔ Brew stopped"
```

Add to dashboard:
```yaml
type: button
name: Stop Brew
icon: mdi:stop-circle
tap_action:
	action: call-service
	service: script.meticulous_emergency_stop
hold_action:
	action: none
```

---

## Shot Tracking & Analysis

### Daily Shot Counter

Track how many shots you pull each day.

```yaml
input_number:
	daily_shot_count:
		name: "Daily Shot Count"
		min: 0
		max: 50
		step: 1
		icon: mdi:counter

automation:
	- id: count_daily_shots
		alias: "Meticulous: Count Daily Shots"
		trigger:
			- platform: state
				entity_id: binary_sensor.meticulous_brewing
				from: "on"
				to: "off"
		action:
			- service: input_number.increment
				target:
					entity_id: input_number.daily_shot_count

	- id: reset_daily_shot_count
		alias: "Meticulous: Reset Daily Count"
		trigger:
			- platform: time
				at: "00:00:00"
		action:
			- service: input_number.set_value
				target:
					entity_id: input_number.daily_shot_count
				data:
					value: 0
```

### Shot Quality Trend Tracking

Log shot ratings over time for analysis.

```yaml
automation:
	- id: track_shot_quality
		alias: "Meticulous: Track Shot Quality"
		description: "Log shot metrics for trend analysis"
		trigger:
			- platform: state
				entity_id: sensor.meticulous_last_shot_rating
		condition:
			- condition: template
				value_template: "{{ trigger.to_state.state != 'unknown' }}"
		action:
			- service: logbook.log
				data:
					name: "Shot Quality"
					message: >
						{{ states('sensor.meticulous_active_profile') }}:
						{{ states('sensor.meticulous_shot_weight') }}g in {{ states('sensor.meticulous_shot_timer') }}s
						Rating: {{ states('sensor.meticulous_last_shot_rating') }}
```

### Maintenance Reminder

Track total shots pulled and remind about periodic maintenance.

```yaml
automation:
	- id: maintenance_reminder
		alias: "Meticulous: Maintenance Reminder"
		description: "Remind to clean after 200 shots"
		trigger:
			- platform: numeric_state
				entity_id: sensor.meticulous_total_shots
				above: 200
		condition:
			- condition: template
				value_template: >
					{{ (states('sensor.meticulous_total_shots') | int) % 200 == 0 }}
		action:
			- service: persistent_notification.create
				data:
					title: "☕ Maintenance Time"
					message: >
						You've pulled {{ states('sensor.meticulous_total_shots') }} shots!

						Suggested maintenance:
						- Clean the chamber and piston
						- Wipe down the brew head
						- Check for scale buildup
						- Clean the drip tray
					notification_id: meticulous_maintenance
```

### Caffeine Intake Tracking

Monitor your daily caffeine consumption.

```yaml
input_number:
	daily_caffeine_mg:
		name: "Daily Caffeine (mg)"
		min: 0
		max: 1000
		step: 1
		unit_of_measurement: "mg"
		icon: mdi:coffee

automation:
	- id: track_caffeine
		alias: "Meticulous: Track Caffeine"
		description: "Add ~64mg per double shot"
		trigger:
			- platform: state
				entity_id: binary_sensor.meticulous_brewing
				from: "on"
				to: "off"
		action:
			- service: input_number.set_value
				target:
					entity_id: input_number.daily_caffeine_mg
				data:
					value: "{{ states('input_number.daily_caffeine_mg') | int + 64 }}"

	- id: caffeine_warning
		alias: "Meticulous: Caffeine Warning"
		trigger:
			- platform: numeric_state
				entity_id: input_number.daily_caffeine_mg
				above: 400
		action:
			- service: notify.mobile_app_phone
				data:
					message: "⚠️ Daily caffeine over 400mg - consider switching to decaf!"

	- id: reset_caffeine_count
		alias: "Meticulous: Reset Caffeine"
		trigger:
			- platform: time
				at: "00:00:00"
		action:
			- service: input_number.set_value
				target:
					entity_id: input_number.daily_caffeine_mg
				data:
					value: 0
```

---

## Voice Control

### Voice-Activated Profile Brewing

Start brewing with a specific profile using voice commands.

**Create input_boolean triggers for each profile:**
```yaml
input_boolean:
	brew_turbo_bloom:
		name: "Brew Turbo Bloom"
		icon: mdi:lightning-bolt
	brew_traditional_italian:
		name: "Brew Traditional Italian"
		icon: mdi:coffee-maker
	brew_soup:
		name: "Brew Soup"
		icon: mdi:bowl-mix
	brew_light_roast:
		name: "Brew Light Roast"
		icon: mdi:weather-sunny
```

**Create automations for each profile:**
```yaml
automation:
	- id: voice_brew_turbo_bloom
		alias: "Voice: Brew Turbo Bloom"
		trigger:
			- platform: state
				entity_id: input_boolean.brew_turbo_bloom
				to: "on"
		action:
			- service: meticulous.load_profile
				data:
					profile_id: "turbo-bloom-id"
			- delay: "00:00:01"
			- service: meticulous.start_brew
			- delay: "00:00:01"
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.brew_turbo_bloom

	- id: voice_brew_traditional_italian
		alias: "Voice: Brew Traditional Italian"
		trigger:
			- platform: state
				entity_id: input_boolean.brew_traditional_italian
				to: "on"
		action:
			- service: meticulous.load_profile
				data:
					profile_id: "traditional-italian-id"
			- delay: "00:00:01"
			- service: meticulous.start_brew
			- delay: "00:00:01"
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.brew_traditional_italian

	- id: voice_brew_soup
		alias: "Voice: Brew Soup"
		trigger:
			- platform: state
				entity_id: input_boolean.brew_soup
				to: "on"
		action:
			- service: meticulous.load_profile
				data:
					profile_id: "soup-id"
			- delay: "00:00:01"
			- service: meticulous.start_brew
			- delay: "00:00:01"
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.brew_soup

	- id: voice_brew_light_roast
		alias: "Voice: Brew Light Roast"
		trigger:
			- platform: state
				entity_id: input_boolean.brew_light_roast
				to: "on"
		action:
			- service: meticulous.load_profile
				data:
					profile_id: "light-roast-id"
			- delay: "00:00:01"
			- service: meticulous.start_brew
			- delay: "00:00:01"
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.brew_light_roast
```

**Set up custom routines in Google Home or Alexa:**

For Google Home, create a Routine that triggers on voice input and executes a scene or calls a service. Example mappings:
- Voice: "Let's pull a soup shot" → Triggers `brew_soup` boolean
- Voice: "Let's do a turbo bloom" → Triggers `brew_turbo_bloom` boolean
- Voice: "Make a traditional italian espresso" → Triggers `brew_traditional_italian` boolean
- Voice: "Let's brew a light roast" → Triggers `brew_light_roast` boolean

For Alexa, use Routines similarly:
- Voice: "Let's pull a soup shot" → Turns on `brew_soup`
- Voice: "Let's do a turbo bloom" → Turns on `brew_turbo_bloom`
- Voice: "Traditional italian espresso" → Turns on `brew_traditional_italian`

This creates natural, conversational commands instead of generic "turn on" phrases.

### Quick Profile Switch (Voice)

Switch profiles without starting a brew.

```yaml
input_boolean:
	load_turbo_bloom_profile:
		name: "Load Turbo Bloom Profile"
		icon: mdi:lightning-bolt
	load_traditional_italian_profile:
		name: "Load Traditional Italian Profile"
		icon: mdi:coffee-maker

automation:
	- id: voice_load_turbo_bloom
		alias: "Voice: Load Turbo Bloom"
		trigger:
			- platform: state
				entity_id: input_boolean.load_turbo_bloom_profile
				to: "on"
		action:
			- service: meticulous.load_profile
				data:
					profile_id: "turbo-bloom-id"
			- service: notify.mobile_app_phone
				data:
					message: "Turbo Bloom profile loaded"
			- delay: "00:00:01"
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.load_turbo_bloom_profile

	- id: voice_load_traditional_italian
		alias: "Voice: Load Traditional Italian"
		trigger:
			- platform: state
				entity_id: input_boolean.load_traditional_italian_profile
				to: "on"
		action:
			- service: meticulous.load_profile
				data:
					profile_id: "traditional-italian-id"
			- service: notify.mobile_app_phone
				data:
					message: "Traditional Italian profile loaded"
			- delay: "00:00:01"
			- service: input_boolean.turn_off
				target:
					entity_id: input_boolean.load_traditional_italian_profile
```

---

## Advanced Automations

### Presence-Based Profile Loading

Automatically load different profiles based on who's home (each person has their preference).

```yaml
automation:
	- id: user_presence_profile
		alias: "Meticulous: User Presence Profile"
		description: "Load profile based on who's home"
		trigger:
			- platform: state
				entity_id: person.user1
				to: "home"
			- platform: state
				entity_id: person.user2
				to: "home"
		action:
			- choose:
					- conditions:
							- condition: state
								entity_id: person.user1
								state: "home"
							- condition: state
								entity_id: person.user2
								state: "not_home"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "user1-favorite-id"
							- service: notify.mobile_app_phone
								data:
									message: "Loaded User 1's profile"
					- conditions:
							- condition: state
								entity_id: person.user2
								state: "home"
							- condition: state
								entity_id: person.user1
								state: "not_home"
						sequence:
							- service: meticulous.load_profile
								data:
									profile_id: "user2-favorite-id"
							- service: notify.mobile_app_phone
								data:
									message: "Loaded User 2's profile"
```

### Shot Timer Live Display

Show a live brewing timer on your dashboard (only visible during brewing).

```yaml
type: conditional
conditions:
	- entity: binary_sensor.meticulous_brewing
		state: "on"
cards:
	- type: entities
		title: "⏱️ Brewing in Progress"
		entities:
			- entity: sensor.meticulous_shot_timer
				name: "Shot Time"
				icon: mdi:timer-sand
			- entity: sensor.meticulous_pressure
				name: "Pressure"
				icon: mdi:gauge
			- entity: sensor.meticulous_flow_rate
				name: "Flow Rate"
				icon: mdi:water-pump
			- entity: sensor.meticulous_shot_weight
				name: "Current Weight"
				icon: mdi:scale
```

### Shot Weight Target Alert

Notify when shot reaches target weight (useful if you want to stop early or extend).

```yaml
input_number:
	target_shot_weight:
		name: "Target Shot Weight"
		min: 15
		max: 60
		step: 1
		unit_of_measurement: "g"
		initial: 36

automation:
	- id: target_weight_alert
		alias: "Meticulous: Target Weight Reached"
		trigger:
			- platform: numeric_state
				entity_id: sensor.meticulous_shot_weight
				above: input_number.target_shot_weight
		condition:
			- condition: state
				entity_id: binary_sensor.meticulous_brewing
				state: "on"
		action:
			- service: notify.mobile_app_phone
				data:
					message: "🎯 Target weight reached: {{ states('sensor.meticulous_shot_weight') }}g"
					data:
						ttl: 0
						priority: high
```

### Multiple Daily Shots Tracker with Timestamps

Log each shot with a timestamp for detailed tracking.

```yaml
input_text:
	todays_shots_log:
		name: "Today's Shots Log"
		max: 255

automation:
	- id: log_shot_timestamp
		alias: "Meticulous: Log Shot Timestamp"
		trigger:
			- platform: state
				entity_id: binary_sensor.meticulous_brewing
				from: "on"
				to: "off"
		action:
			- service: input_text.set_value
				target:
					entity_id: input_text.todays_shots_log
				data:
					value: >
						{{ states('input_text.todays_shots_log') }}
						{{ now().strftime('%H:%M') }}: {{ states('sensor.meticulous_shot_weight') }}g |

	- id: clear_shot_log
		alias: "Meticulous: Clear Shot Log"
		trigger:
			- platform: time
				at: "00:00:00"
		action:
			- service: input_text.set_value
				target:
					entity_id: input_text.todays_shots_log
				data:
					value: ""
```

---

## Complete Dashboard Example

Full Meticulous dashboard with status, controls, and live metrics.

```yaml
type: vertical-stack
title: "☕ Meticulous Espresso"
cards:
	# Status Card
	- type: entities
		title: "Status"
		entities:
			- entity: sensor.meticulous_state
				name: "Machine State"
			- entity: binary_sensor.meticulous_brewing
				name: "Brewing"
			- entity: sensor.meticulous_active_profile
				name: "Active Profile"
			- entity: binary_sensor.meticulous_connected
				name: "Connection"

	# Control Buttons
	- type: horizontal-stack
		cards:
			- type: button
				name: "Tare"
				icon: mdi:scale-balance
				tap_action:
					action: call-service
					service: meticulous.tare_scale
			- type: button
				name: "Start"
				icon: mdi:play-circle
				tap_action:
					action: call-service
					service: script.meticulous_quick_brew
			- type: button
				name: "Stop"
				icon: mdi:stop-circle
				tap_action:
					action: call-service
					service: meticulous.stop_brew

	# Profile Selector
	- type: entities
		title: "Profile"
		entities:
			- entity: input_select.meticulous_profile

	# Live Brewing (conditional)
	- type: conditional
		conditions:
			- entity: binary_sensor.meticulous_brewing
				state: "on"
		card:
			type: entities
			title: "⏱️ Brewing Live"
			entities:
				- entity: sensor.meticulous_shot_timer
					name: "Time"
				- entity: sensor.meticulous_pressure
					name: "Pressure"
				- entity: sensor.meticulous_flow_rate
					name: "Flow"
				- entity: sensor.meticulous_shot_weight
					name: "Weight"

	# Statistics Card
	- type: entities
		title: "Statistics"
		entities:
			- entity: sensor.meticulous_total_shots
				name: "Total Shots"
				icon: mdi:counter
			- entity: input_number.daily_shot_count
				name: "Today's Shots"
			- entity: sensor.meticulous_last_shot_name
				name: "Last Shot"
			- entity: sensor.meticulous_last_shot_rating
				name: "Last Rating"
			- entity: input_number.daily_caffeine_mg
				name: "Caffeine Today"
```

---

## Troubleshooting Automations

### Common Issues

- **Automation not triggering**: Verify conditions are met, entity IDs are correct, and automation is enabled
- **Service calls failing**: Verify add-on is running and machine is connected
- **Notifications not received**: Check mobile app configuration and notification permissions
- **Delays feel too long/short**: Adjust delay times based on your machine's actual response time
- **Input helpers resetting**: Check if you have competing automations or manual changes

### Debugging Tips

1. Enable debug logging in the add-on configuration
2. Use Developer Tools → Services to test individual service calls
3. Check the Home Assistant logs for automation errors
4. Use the Trace feature in automation settings to see execution flow
5. Test with simple notify actions first before complex logic

---

## Resources

- Home Assistant Automation Documentation: https://www.home-assistant.io/docs/automation/
- Template Documentation: https://www.home-assistant.io/docs/configuration/templating/
- Script Syntax: https://www.home-assistant.io/docs/scripts/
- Lovelace Cards: https://www.home-assistant.io/lovelace/
- Meticulous Official Site: https://meticulous.coffee/
- Meticulous Discord Community: [Link to be added]
