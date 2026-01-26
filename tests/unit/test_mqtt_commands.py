"""Unit tests for MQTT command handlers."""

import json
import os
import sys
import unittest
from unittest.mock import Mock

from meticulous.api_types import ActionType, APIError

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rootfs", "usr", "bin"))

# These imports will show as unresolved but work at runtime
# due to dynamic path manipulation above
# pyright: reportMissingImports=false
from mqtt_commands import (  # noqa: E402  # type: ignore
    handle_command_continue_brew,
    handle_command_enable_sounds,
    handle_command_load_profile,
    handle_command_preheat,
    handle_command_set_brightness,
    handle_command_start_brew,
    handle_command_stop_brew,
    handle_command_tare_scale,
    mqtt_on_message,
)


class TestMQTTCommands(unittest.TestCase):
    """Test MQTT command handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.addon = Mock()
        self.addon.api = Mock()
        self.addon.command_prefix = "meticulous_espresso/command"
        # Mock async methods to avoid "coroutine expected" errors
        self.addon.update_settings = Mock(return_value=None)
        self.addon.update_profile_info = Mock(return_value=None)
        self.client = Mock()
        self.userdata = None

    def test_start_brew_success(self):
        """Test successful start_brew command."""
        self.addon.api.execute_action.return_value = {"success": True}
        handle_command_start_brew(self.addon)
        self.addon.api.execute_action.assert_called_once_with(ActionType.START)

    def test_start_brew_no_api(self):
        """Test start_brew with no API connection."""
        self.addon.api = None
        handle_command_start_brew(self.addon)
        # Should log error but not crash

    def test_start_brew_api_error(self):
        """Test start_brew with API error."""
        error = APIError(error="Connection failed")
        self.addon.api.execute_action.return_value = error
        handle_command_start_brew(self.addon)
        self.addon.api.execute_action.assert_called_once()

    def test_stop_brew_success(self):
        """Test successful stop_brew command."""
        self.addon.api.execute_action.return_value = {"success": True}
        handle_command_stop_brew(self.addon)
        self.addon.api.execute_action.assert_called_once_with(ActionType.STOP)

    def test_continue_brew_success(self):
        """Test successful continue_brew command."""
        self.addon.api.execute_action.return_value = {"success": True}
        handle_command_continue_brew(self.addon)
        self.addon.api.execute_action.assert_called_once_with(ActionType.CONTINUE)

    def test_preheat_success(self):
        """Test successful preheat command."""
        self.addon.api.execute_action.return_value = {"success": True}
        handle_command_preheat(self.addon)
        self.addon.api.execute_action.assert_called_once_with(ActionType.PREHEAT)

    def test_tare_scale_success(self):
        """Test successful tare_scale command."""
        self.addon.api.execute_action.return_value = {"success": True}
        handle_command_tare_scale(self.addon)
        self.addon.api.execute_action.assert_called_once_with(ActionType.TARE)

    def test_load_profile_success(self):
        """Test successful load_profile command."""
        # Setup: profile name comes from HA, we need available_profiles to map name->id
        self.addon.available_profiles = {
            "profile-id-123": "Espresso",
            "profile-id-456": "Americano",
        }
        # send_profile_hover always returns None (success indication is absence of error)
        self.addon.api.send_profile_hover.return_value = None
        handle_command_load_profile(self.addon, "Espresso")
        # Verify send_profile_hover was called with correct payload
        self.addon.api.send_profile_hover.assert_called_once()
        call_args = self.addon.api.send_profile_hover.call_args[0][0]
        self.assertEqual(call_args["id"], "profile-id-123")
        self.assertEqual(call_args["from"], "app")
        self.assertEqual(call_args["type"], "focus")

    def test_load_profile_empty_id(self):
        """Test load_profile with empty profile name."""
        self.addon.available_profiles = {}
        handle_command_load_profile(self.addon, "")
        self.addon.api.send_profile_hover.assert_not_called()

    def test_set_brightness_integer_payload(self):
        """Test set_brightness with integer payload."""
        # set_brightness returns None on success (by design in pymeticulous)
        self.addon.api.set_brightness.return_value = None
        handle_command_set_brightness(self.addon, "75")
        self.addon.api.set_brightness.assert_called_once()
        args = self.addon.api.set_brightness.call_args[0][0]
        self.assertEqual(args.brightness, 75)

    def test_set_brightness_json_payload(self):
        """Test set_brightness with JSON payload."""
        # set_brightness returns None on success (by design in pymeticulous)
        self.addon.api.set_brightness.return_value = None
        payload = json.dumps({"brightness": 50, "interpolation": "linear", "animation_time": 1000})
        handle_command_set_brightness(self.addon, payload)
        self.addon.api.set_brightness.assert_called_once()
        args = self.addon.api.set_brightness.call_args[0][0]
        self.assertEqual(args.brightness, 50)
        self.assertEqual(args.interpolation, "linear")
        self.assertEqual(args.animation_time, 1000)

    def test_enable_sounds_true(self):
        """Test enable_sounds with true value."""
        # update_setting returns None or an object, not {"success": True}
        self.addon.api.update_setting.return_value = None
        for payload in ["true", "1", "on", "yes", "TRUE"]:
            self.addon.api.update_setting.reset_mock()
            handle_command_enable_sounds(self.addon, payload)
            self.addon.api.update_setting.assert_called_once()
            args = self.addon.api.update_setting.call_args[0][0]
            self.assertTrue(args.enable_sounds)

    def test_enable_sounds_false(self):
        """Test enable_sounds with false value."""
        # update_setting returns None or an object, not {"success": True}
        self.addon.api.update_setting.return_value = None
        for payload in ["false", "0", "off", "no", "FALSE"]:
            self.addon.api.update_setting.reset_mock()
            handle_command_enable_sounds(self.addon, payload)
            self.addon.api.update_setting.assert_called_once()
            args = self.addon.api.update_setting.call_args[0][0]
            self.assertFalse(args.enable_sounds)

    def test_mqtt_on_message_start_brew(self):
        """Test MQTT message routing for start_brew."""
        msg = Mock()
        msg.topic = f"{self.addon.command_prefix}/start_brew"
        msg.payload = b""
        self.addon.api.execute_action.return_value = {"success": True}

        mqtt_on_message(self.addon, self.client, self.userdata, msg)
        self.addon.api.execute_action.assert_called_once_with(ActionType.START)

    def test_mqtt_on_message_unknown_topic(self):
        """Test MQTT message routing for unknown topic."""
        msg = Mock()
        msg.topic = f"{self.addon.command_prefix}/unknown_command"
        msg.payload = b""

        # Should not raise exception, just log warning
        mqtt_on_message(self.addon, self.client, self.userdata, msg)

    def test_mqtt_on_message_exception_handling(self):
        """Test MQTT message exception handling."""
        msg = Mock()
        msg.topic = f"{self.addon.command_prefix}/start_brew"
        msg.payload.decode.side_effect = Exception("Decode failed")

        # Should not raise exception, just log error
        mqtt_on_message(self.addon, self.client, self.userdata, msg)


class TestCommandValidation(unittest.TestCase):
    """Test command validation and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.addon = Mock()
        self.addon.api = Mock()

    def test_set_brightness_invalid_json(self):
        """Test set_brightness with invalid JSON."""
        self.addon.api.set_brightness.return_value = {"success": True}
        # Should handle gracefully and not crash
        try:
            handle_command_set_brightness(self.addon, "{invalid json")
        except Exception:
            self.fail("Should handle invalid JSON gracefully")

    def test_set_brightness_out_of_range(self):
        """Test set_brightness with out-of-range value."""
        # set_brightness returns None on success
        self.addon.api.set_brightness.return_value = None
        # API should validate, but our handler should not crash
        handle_command_set_brightness(self.addon, "150")
        self.addon.api.set_brightness.assert_called_once()

    def test_all_commands_with_no_api(self):
        """Test all commands handle missing API gracefully."""
        self.addon.api = None

        # None of these should raise exceptions
        handle_command_start_brew(self.addon)
        handle_command_stop_brew(self.addon)
        handle_command_continue_brew(self.addon)
        handle_command_preheat(self.addon)
        handle_command_tare_scale(self.addon)
        handle_command_load_profile(self.addon, "test-id")
        handle_command_set_brightness(self.addon, "50")
        handle_command_enable_sounds(self.addon, "true")


if __name__ == "__main__":
    unittest.main()

# ...rest of the file unchanged...
