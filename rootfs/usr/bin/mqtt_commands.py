"""MQTT command handlers for Meticulous Espresso Add-on services."""

import asyncio
import json
import logging
from typing import TYPE_CHECKING

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
    try:
        # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
        # The wrapper has a bug (PR #20) where it uses string repr of ActionType enum
        # instead of ActionType.value, producing /api/v1/action/ActionType.START
        # instead of /api/v1/action/start. Using direct HTTP bypasses this.
        response = addon.api.session.get(f"{addon.api.base_url}/api/v1/action/start")
        result = response.json()
        status = result.get("status")
        if status == "ok":
            logger.info("start_brew: Success")
        else:
            logger.error(f"start_brew failed with status: {status}")
    except Exception as e:
        logger.error(f"start_brew error: {e}", exc_info=True)


def handle_command_stop_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot stop brew: API not connected")
        return
    try:
        # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
        # The wrapper has a bug (PR #20) where it uses string repr of ActionType enum
        # instead of ActionType.value, producing /api/v1/action/ActionType.STOP
        # instead of /api/v1/action/stop. Using direct HTTP bypasses this.
        response = addon.api.session.get(f"{addon.api.base_url}/api/v1/action/stop")
        result = response.json()
        status = result.get("status")
        if status == "ok":
            logger.info("stop_brew: Success")
        else:
            logger.error(f"stop_brew failed with status: {status}")
    except Exception as e:
        logger.error(f"stop_brew error: {e}", exc_info=True)


def handle_command_continue_brew(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot continue brew: API not connected")
        return
    try:
        # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
        # The wrapper has a bug (PR #20) where it uses string repr of ActionType enum
        # instead of ActionType.value, producing /api/v1/action/ActionType.CONTINUE
        # instead of /api/v1/action/continue. Using direct HTTP bypasses this.
        response = addon.api.session.get(f"{addon.api.base_url}/api/v1/action/continue")
        result = response.json()
        status = result.get("status")
        if status == "ok":
            logger.info("continue_brew: Success")
        else:
            logger.error(f"continue_brew failed with status: {status}")
    except Exception as e:
        logger.error(f"continue_brew error: {e}", exc_info=True)


def handle_command_preheat(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot preheat: API not connected")
        return
    try:
        # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
        # The wrapper has a bug (PR #20) where it uses string repr of ActionType enum
        # instead of ActionType.value, producing /api/v1/action/ActionType.PREHEAT
        # instead of /api/v1/action/preheat. Using direct HTTP bypasses this.
        response = addon.api.session.get(f"{addon.api.base_url}/api/v1/action/preheat")
        result = response.json()
        status = result.get("status")
        if status == "ok":
            logger.info("preheat: Success")
        else:
            logger.error(f"preheat failed with status: {status}")
    except Exception as e:
        logger.error(f"preheat error: {e}", exc_info=True)


def handle_command_tare_scale(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot tare scale: API not connected")
        return
    try:
        # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
        # The wrapper has a bug (PR #20) where it uses string repr of ActionType enum
        # instead of ActionType.value, producing /api/v1/action/ActionType.TARE
        # instead of /api/v1/action/tare. Using direct HTTP bypasses this.
        response = addon.api.session.get(f"{addon.api.base_url}/api/v1/action/tare")
        result = response.json()
        status = result.get("status")
        if status == "ok":
            logger.info("tare_scale: Success")
        else:
            logger.error(f"tare_scale failed with status: {status}")
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

        payload = {
            "id": profile_id,
            "from": "app",
            "type": "focus",
        }
        addon.api.send_profile_hover(payload)
        logger.info(f"load_profile: Set active profile ({profile_name})")
        _run_or_schedule(addon.update_profile_info())
    except Exception as e:
        logger.error(f"load_profile error: {e}", exc_info=True)


def handle_command_set_brightness(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot set brightness: API not connected")
        return
    try:
        data = json.loads(payload) if payload.startswith("{") else {"brightness": int(payload)}
        brightness_value = data.get("brightness", 50)

        # Convert from 0-100 range to 0-1.0 range that the backend expects
        brightness_normalized = brightness_value / 100.0

        # Call the HTTP endpoint directly
        request_data = {
            "brightness": brightness_normalized,
            "interpolation": data.get("interpolation", "curve"),
            "animation_time": data.get("animation_time", 500) / 1000.0,  # Convert ms to seconds
        }
        response = addon.api.session.post(
            f"{addon.api.base_url}/api/v1/machine/backlight", json=request_data
        )

        if response.status_code == 200:
            logger.info(f"set_brightness: Success ({brightness_value})")
            # Immediately publish the new brightness state
            _run_or_schedule(addon.publish_to_homeassistant({"brightness": brightness_value}))
        else:
            logger.error(
                f"set_brightness failed with status {response.status_code}: " f"{response.text}"
            )
    except Exception as e:
        logger.error(f"set_brightness error: {e}", exc_info=True)


def handle_command_enable_sounds(addon: "MeticulousAddon", payload: str):
    if not addon.api:
        logger.error("Cannot enable/disable sounds: API not connected")
        return
    try:
        enabled = payload.lower() in ("true", "1", "on", "yes")
        try:
            # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
            # The wrapper tries to deserialize settings response which may have schema
            # mismatches. Direct HTTP gives us full control over response handling.
            request_data = {"enable_sounds": enabled}
            response = addon.api.session.post(
                f"{addon.api.base_url}/api/v1/settings", json=request_data
            )
            if response.status_code == 200:
                logger.info(f"enable_sounds: Success ({enabled})")
                _run_or_schedule(addon.update_settings())
            else:
                logger.error(
                    f"enable_sounds failed with status {response.status_code}: " f"{response.text}"
                )
        except Exception as e:
            logger.error(f"enable_sounds error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"enable_sounds error: {e}", exc_info=True)


def handle_command_reboot_machine(addon: "MeticulousAddon"):
    if not addon.api:
        logger.error("Cannot reboot machine: API not connected")
        return
    try:
        # Call the HTTP endpoint directly instead of using pymeticulous wrapper.
        # The wrapper tries to deserialize reboot response which may have schema
        # mismatches. Direct HTTP gives us full control over response handling.
        response = addon.api.session.post(f"{addon.api.base_url}/api/v1/machine/reboot")
        if response.status_code == 200:
            logger.info("reboot_machine: Success")
        else:
            logger.error(
                f"reboot_machine failed with status {response.status_code}: " f"{response.text}"
            )
    except Exception as e:
        logger.error(f"reboot_machine error: {e}", exc_info=True)


def _run_or_schedule(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
