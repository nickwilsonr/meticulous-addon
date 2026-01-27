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

        if topic == f"{addon.command_prefix}/start_brew":
            handle_command_start_brew(addon)
        elif topic == f"{addon.command_prefix}/stop_brew":
            handle_command_stop_brew(addon)
        elif topic == f"{addon.command_prefix}/continue_brew":
            handle_command_continue_brew(addon)
        elif topic == f"{addon.command_prefix}/preheat":
            handle_command_preheat(addon)
        elif topic == f"{addon.command_prefix}/tare_scale":
            handle_command_tare_scale(addon)
        elif topic == f"{addon.command_prefix}/load_profile":
            handle_command_load_profile(addon, payload)
        elif topic == f"{addon.command_prefix}/set_brightness":
            handle_command_set_brightness(addon, payload)
        elif topic == f"{addon.command_prefix}/enable_sounds":
            handle_command_enable_sounds(addon, payload)
        else:
            logger.warning(f"Unknown command topic: {topic}")
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}", exc_info=True)


def handle_command_start_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot start brew: API not connected")
        return
    try:
        logger.debug("Executing START action...")
        result = addon.api.execute_action(ActionType.START)
        logger.debug(f"execute_action returned: {result}, type: {type(result)}")
        if isinstance(result, APIError):
            logger.error(f"start_brew failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"start_brew failed: action returned status '{result.status}'")
        else:
            logger.info("start_brew: Success")
    except Exception as e:
        logger.error(f"start_brew error: {e}", exc_info=True)


def handle_command_stop_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot stop brew: API not connected")
        return
    try:
        result = addon.api.execute_action(ActionType.STOP)
        if isinstance(result, APIError):
            logger.error(f"stop_brew failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"stop_brew failed: action returned status '{result.status}'")
        else:
            logger.info("stop_brew: Success")
    except Exception as e:
        logger.error(f"stop_brew error: {e}", exc_info=True)


def handle_command_continue_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot continue brew: API not connected")
        return
    try:
        result = addon.api.execute_action(ActionType.CONTINUE)
        if isinstance(result, APIError):
            logger.error(f"continue_brew failed: {result.error}")
        elif result.status != "ok":
            logger.error(f"continue_brew failed: action returned status '{result.status}'")
        else:
            logger.info("continue_brew: Success")
    except Exception as e:
        logger.error(f"continue_brew error: {e}", exc_info=True)


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


def handle_command_load_profile(addon: "MeticulousAddon", profile_name: str):
    if not addon.api:
        logger.error("Cannot load profile: API not connected")
        return
    if not profile_name:
        logger.error("load_profile: missing profile_name")
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
            logger.error(f"load_profile: Unknown profile name: {profile_name}")
            return

        # Send profileHover to select the profile without starting a shot
        # (load_profile_by_id() would actually start the shot, which we don't want)
        payload = {"id": profile_id, "from": "app", "type": "focus"}
        addon.api.send_profile_hover(payload)
        # send_profile_hover always returns None (not error on failure)
        logger.info(f"load_profile: Successfully selected profile ({profile_name})")
    except Exception as e:
        logger.error(f"load_profile error: {e}", exc_info=True)


def handle_command_set_brightness(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot set brightness: API not connected")
        return
    try:
        data = json.loads(payload) if payload.startswith("{") else {"brightness": int(payload)}
        brightness_value = int(data.get("brightness", 50))

        # Normalize brightness from 0-100 (HA range) to 0-1 (pyMeticulous range)
        brightness_normalized = float(brightness_value) / 100.0

        # Use the pyMeticulous API wrapper
        # Note: BrightnessRequest expects brightness as float (0-1 range)
        brightness_request = BrightnessRequest(
            brightness=brightness_normalized,
            interpolation=str(data.get("interpolation", "curve")),
            animation_time=int(data.get("animation_time", 500)),  # Keep as ms
        )
        result = addon.api.set_brightness(brightness_request)

        # set_brightness returns None on success, Optional[APIError] on failure
        if isinstance(result, APIError):
            logger.error(f"set_brightness failed: {result.error}")
        else:
            logger.info(f"set_brightness: Success ({brightness_value}%)")
            # Immediately publish the new brightness state (in 0-100 range for HA)
            _run_or_schedule(addon.publish_to_homeassistant({"brightness": brightness_value}))
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
