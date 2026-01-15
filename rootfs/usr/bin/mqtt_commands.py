"""MQTT command handlers for Meticulous Espresso Add-on services."""

import asyncio
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from run import MeticulousAddon

from meticulous.api_types import ActionType, APIError, BrightnessRequest, PartialSettings

logger = logging.getLogger(__name__)


def mqtt_on_message(addon: "MeticulousAddon", client, userdata, msg):
    """Handle incoming MQTT messages for commands."""
    try:
        topic = msg.topic
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
        elif topic == f"{addon.command_prefix}/reboot_machine":
            handle_command_reboot_machine(addon)
        else:
            logger.warning(f"Unknown command topic: {topic}")
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}", exc_info=True)


def handle_command_start_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot start brew: API not connected")
        return
    result = addon.api.execute_action(ActionType.START)
    if isinstance(result, APIError):
        logger.error(f"start_brew failed: {result.error}")
    else:
        logger.info("start_brew: Success")


def handle_command_stop_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot stop brew: API not connected")
        return
    result = addon.api.execute_action(ActionType.STOP)
    if isinstance(result, APIError):
        logger.error(f"stop_brew failed: {result.error}")
    else:
        logger.info("stop_brew: Success")


def handle_command_continue_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot continue brew: API not connected")
        return
    result = addon.api.execute_action(ActionType.CONTINUE)
    if isinstance(result, APIError):
        logger.error(f"continue_brew failed: {result.error}")
    else:
        logger.info("continue_brew: Success")


def handle_command_preheat(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot preheat: API not connected")
        return
    result = addon.api.execute_action(ActionType.PREHEAT)
    if isinstance(result, APIError):
        logger.error(f"preheat failed: {result.error}")
    else:
        logger.info("preheat: Success")


def handle_command_tare_scale(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot tare scale: API not connected")
        return
    result = addon.api.execute_action(ActionType.TARE)
    if isinstance(result, APIError):
        logger.error(f"tare_scale failed: {result.error}")
    elif result is None:
        logger.error("tare_scale: returned None (unexpected)")
    else:
        status = getattr(result, "status", None)
        logger.info(f"tare_scale: Success (status={status})")


def handle_command_load_profile(addon: "MeticulousAddon", profile_id: str):
    if not addon.api:
        logger.error("Cannot load profile: API not connected")
        return
    if not profile_id:
        logger.error("load_profile: missing profile_id")
        return
    try:
        payload = {
            "id": profile_id,
            "from": "app",
            "type": "focus",
        }
        addon.api.send_profile_hover(payload)
        logger.info(f"load_profile: Set active profile ({profile_id})")
        _run_or_schedule(addon.update_profile_info())
    except Exception as e:
        logger.error(f"load_profile error: {e}", exc_info=True)


def handle_command_set_brightness(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot set brightness: API not connected")
        return
    try:
        data = json.loads(payload) if payload.startswith("{") else {"brightness": int(payload)}
        interpolation_value = data.get("interpolation", "curve")
        brightness_req = BrightnessRequest(
            brightness=data.get("brightness", 50),
            interpolation=str(interpolation_value) if interpolation_value is not None else "curve",
            animation_time=data.get("animation_time", 500),
        )
        result = addon.api.set_brightness(brightness_req)
        if isinstance(result, APIError):
            logger.error(f"set_brightness failed: {result.error}")
        elif result is None:
            logger.info(f"set_brightness: Success ({data.get('brightness')})")
            _run_or_schedule(addon.update_settings())
        else:
            logger.warning(f"set_brightness: Unexpected result type: {type(result)}")
    except Exception as e:
        logger.error(f"set_brightness error: {e}", exc_info=True)


def handle_command_enable_sounds(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot enable/disable sounds: API not connected")
        return
    try:
        enabled = payload.lower() in ("true", "1", "on", "yes")
        settings = PartialSettings(enable_sounds=enabled)
        result = addon.api.update_setting(settings)
        if isinstance(result, APIError):
            logger.error(f"enable_sounds failed: {result.error}")
        else:
            logger.info(f"enable_sounds: Success ({enabled})")
            _run_or_schedule(addon.update_settings())
    except Exception as e:
        logger.error(f"enable_sounds error: {e}", exc_info=True)


def handle_command_reboot_machine(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot reboot machine: API not connected")
        return
    try:
        result = addon.api.reboot_machine()
        if isinstance(result, APIError):
            logger.error(f"reboot_machine failed: {result.error}")
        else:
            logger.info("reboot_machine: Success")
    except Exception as e:
        logger.error(f"reboot_machine error: {e}", exc_info=True)


def _run_or_schedule(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
