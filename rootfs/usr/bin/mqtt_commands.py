"""MQTT command handlers for Meticulous Espresso Add-on services."""

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from meticulous.api_types import ActionType, APIError, BrightnessRequest, PartialSettings

if TYPE_CHECKING:
    from run import MeticulousAddon

logger = logging.getLogger(__name__)


def mqtt_on_message(addon: "MeticulousAddon", client, userdata, msg):
    """Handle incoming MQTT messages for commands."""
    try:
        topic = msg.topic

        # Ignore messages from homeassistant/# (discovery) and only process command messages
        if not topic.startswith(f"{addon.command_prefix}/"):
            logger.debug(f"Ignoring non-command MQTT message: {topic}")
            return

        payload = msg.payload.decode("utf-8")
        logger.debug(f"MQTT command received: {topic} = {payload}")

        if topic == f"{addon.command_prefix}/start_shot":
            handle_command_start_shot(addon)
        elif topic == f"{addon.command_prefix}/stop_shot":
            handle_command_stop_shot(addon)
        elif topic == f"{addon.command_prefix}/continue_shot":
            handle_command_continue_shot(addon)
        elif topic == f"{addon.command_prefix}/abort_shot":
            handle_command_abort_shot(addon)
        elif topic == f"{addon.command_prefix}/preheat":
            handle_command_preheat(addon)
        elif topic == f"{addon.command_prefix}/tare_scale":
            handle_command_tare_scale(addon)
        elif topic == f"{addon.command_prefix}/home_plunger":
            handle_command_home_plunger(addon)
        elif topic == f"{addon.command_prefix}/purge":
            handle_command_purge(addon)
        elif topic == f"{addon.command_prefix}/select_profile":
            handle_command_select_profile(addon, payload)
        elif topic == f"{addon.command_prefix}/run_profile":
            handle_command_run_profile(addon)
        elif topic == f"{addon.command_prefix}/set_brightness":
            handle_command_set_brightness(addon, payload)
        elif topic == f"{addon.command_prefix}/enable_sounds":
            handle_command_enable_sounds(addon, payload)
        else:
            logger.warning(f"Unknown command topic: {topic}")
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}", exc_info=True)


def handle_command_start_shot(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot start shot: API not connected")
        return
    try:
        logger.debug("Executing START action...")
        result = addon.api.execute_action(ActionType.START)
        logger.debug(f"execute_action returned: {result}, type: {type(result)}")
        if isinstance(result, APIError):
            logger.error(f"start_shot failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"start_shot failed: action returned status '{result.status}'")
        else:
            logger.info("start_shot: Success")
    except Exception as e:
        logger.error(f"start_shot error: {e}", exc_info=True)


def handle_command_stop_shot(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot stop shot: API not connected")
        return
    try:
        result = addon.api.execute_action(ActionType.STOP)
        if isinstance(result, APIError):
            logger.error(f"stop_shot failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"stop_shot failed: action returned status '{result.status}'")
        else:
            logger.info("stop_shot: Success")
    except Exception as e:
        logger.error(f"stop_shot error: {e}", exc_info=True)


def handle_command_continue_shot(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot continue shot: API not connected")
        return
    try:
        result = addon.api.execute_action(ActionType.CONTINUE)
        if isinstance(result, APIError):
            logger.error(f"continue_shot failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"continue_shot failed: action returned status '{result.status}'")
        else:
            logger.info("continue_shot: Success")
    except Exception as e:
        logger.error(f"continue_shot error: {e}", exc_info=True)


def handle_command_preheat(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot preheat: API not connected")
        return
    try:
        result = addon.api.execute_action(ActionType.PREHEAT)
        if isinstance(result, APIError):
            logger.error(f"preheat failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"preheat failed: action returned status '{result.status}'")
        else:
            logger.info("preheat: Success")
    except Exception as e:
        logger.error(f"preheat error: {e}", exc_info=True)


def handle_command_tare_scale(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot tare scale: API not connected")
        return
    try:
        logger.debug("Executing TARE action...")
        result = addon.api.execute_action(ActionType.TARE)
        logger.debug(f"execute_action returned: {result}, type: {type(result)}")
        if isinstance(result, APIError):
            logger.error(f"tare_scale failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"tare_scale failed: action returned status '{result.status}'")
        else:
            logger.info("tare_scale: Success")
    except Exception as e:
        logger.error(f"tare_scale error: {e}", exc_info=True)


def handle_command_abort_shot(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot abort shot: API not connected")
        return
    try:
        logger.debug("Executing ABORT action...")
        result = addon.api.execute_action(ActionType.ABORT)
        logger.debug(f"execute_action returned: {result}, type: {type(result)}")
        if isinstance(result, APIError):
            logger.error(f"abort_shot failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"abort_shot failed: action returned status '{result.status}'")
        else:
            logger.info("abort_shot: Success")
    except Exception as e:
        logger.error(f"abort_shot error: {e}", exc_info=True)


def handle_command_home_plunger(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot home plunger: API not connected")
        return
    try:
        logger.debug("Executing HOME action...")
        result = addon.api.execute_action(ActionType.HOME)
        logger.debug(f"execute_action returned: {result}, type: {type(result)}")
        if isinstance(result, APIError):
            logger.error(f"home_plunger failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"home_plunger failed: action returned status '{result.status}'")
        else:
            logger.info("home_plunger: Success")
    except Exception as e:
        logger.error(f"home_plunger error: {e}", exc_info=True)


def handle_command_purge(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot purge: API not connected")
        return
    try:
        logger.debug("Executing PURGE action...")
        result = addon.api.execute_action(ActionType.PURGE)
        logger.debug(f"execute_action returned: {result}, type: {type(result)}")
        if isinstance(result, APIError):
            logger.error(f"purge failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"purge failed: action returned status '{result.status}'")
        else:
            logger.info("purge: Success")
    except Exception as e:
        logger.error(f"purge error: {e}", exc_info=True)


def handle_command_select_profile(addon: "MeticulousAddon", profile_name: str):
    if not addon.api:
        logger.error("Cannot select profile: API not connected")
        return
    if not profile_name:
        logger.error("select_profile: missing profile_name")
        return
    try:
        # profile_name comes from HA select (the value), but we need the ID
        # available_profiles maps id -> name, so we need to find the ID for this name
        profile_id = None
        for pid, pname in addon.available_profiles.items():
            if pname == profile_name:
                profile_id = pid
                break

        if not profile_id:
            logger.error(f"select_profile: Unknown profile name: {profile_name}")
            return

        # Send profileHover to highlight the profile on the machine UI
        # This just selects it visually - user still needs to press button to load
        payload = {"id": profile_id, "from": "app", "type": "focus"}
        addon.api.send_profile_hover(payload)
        # send_profile_hover always returns None (not error on failure)
        logger.info(f"select_profile: Successfully highlighted profile ({profile_name})")

        # Publish state back so HA select entity stays in sync.
        # Without this, HA's stale state prevents re-selecting the previous profile.
        addon.current_profile = profile_name
        if addon.mqtt_client:
            state_topic = f"{addon.state_prefix}/active_profile/state"
            addon.mqtt_client.publish(state_topic, profile_name, qos=1, retain=True)
            logger.debug(f"Published active_profile state: {profile_name}")
    except Exception as e:
        logger.error(f"select_profile error: {e}", exc_info=True)


def handle_command_run_profile(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot run profile: API not connected")
        return
    if not addon.current_profile:
        logger.error("run_profile: No profile currently selected")
        return
    try:
        # Find the profile ID for the current profile name
        profile_id = None
        for pid, pname in addon.available_profiles.items():
            if pname == addon.current_profile:
                profile_id = pid
                break

        if not profile_id:
            logger.error(f"run_profile: Unknown profile: {addon.current_profile}")
            return

        # Load and run the profile
        result = addon.api.load_profile_by_id(profile_id)
        if isinstance(result, APIError):
            logger.error(f"run_profile failed: {result.error}")
        else:
            logger.info(f"run_profile: Successfully started profile ({addon.current_profile})")
    except Exception as e:
        logger.error(f"run_profile error: {e}", exc_info=True)


def handle_command_set_brightness(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot set brightness: API not connected")
        return
    try:
        logger.debug(f"set_brightness raw payload: {payload}")
        data = json.loads(payload) if payload.startswith("{") else {"brightness": int(payload)}
        brightness_value = int(data.get("brightness", 50))
        logger.debug(f"set_brightness parsed: data={data}, brightness_value={brightness_value}")

        # Normalize brightness from 0-100 (HA range) to 0-1 (pyMeticulous range)
        brightness_normalized = float(brightness_value) / 100.0

        # Use the pyMeticulous API wrapper
        # Note: BrightnessRequest expects brightness as float (0-1 range)
        brightness_request = BrightnessRequest(
            brightness=brightness_normalized,
            interpolation=str(data.get("interpolation", "curve")),
            animation_time=int(data.get("animation_time", 500)),  # Keep as ms
        )

        # Workaround for device queue lag: send the command twice
        # Device processes commands asynchronously with a queue, so:
        # 1st send: device returns old value in next event (queue lag)
        # 2nd send: device now returns correct value from 1st command
        result = addon.api.set_brightness(brightness_request)
        if not isinstance(result, APIError):
            # Send again to overcome queue lag
            result = addon.api.set_brightness(brightness_request)

        # set_brightness returns None on success, Optional[APIError] on failure
        if isinstance(result, APIError):
            logger.error(f"set_brightness failed: {result.error}")
        else:
            logger.info(f"set_brightness: Success ({brightness_value}%)")
            # Publish brightness to MQTT immediately so HA UI updates
            # This shows what we requested, even if device takes time to confirm
            if addon.mqtt_client:
                state_topic = f"{addon.state_prefix}/brightness/state"
                addon.mqtt_client.publish(state_topic, str(brightness_value), qos=1, retain=True)
                logger.debug(f"Published brightness state: {brightness_value}%")
    except Exception as e:
        logger.error(f"set_brightness error: {e}", exc_info=True)


def handle_command_enable_sounds(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot enable/disable sounds: API not connected")
        return
    try:
        enabled = payload.lower() in ("true", "1", "on", "yes")
        # Use the pyMeticulous API wrapper
        settings = PartialSettings(enable_sounds=enabled)
        result = addon.api.update_setting(settings)
        if isinstance(result, APIError):
            logger.error(f"enable_sounds failed: {result.error}")
        else:
            logger.info(f"enable_sounds: Success ({enabled})")
            _run_or_schedule(addon.update_settings())
    except Exception as e:
        logger.error(f"enable_sounds error: {e}", exc_info=True)


def _run_or_schedule(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
