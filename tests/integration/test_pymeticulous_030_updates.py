"""Tests for pymeticulous 0.3.0 compatibility updates."""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock

from meticulous.api_types import APIError

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "usr", "bin"))

# pyright: reportMissingImports=false
from mqtt_commands import handle_command_load_profile  # noqa: E402  # type: ignore


class TestProfileLoading(unittest.TestCase):
    """Test profile loading using send_profile_hover instead of load_profile_by_id."""

    def setUp(self):
        """Set up test fixtures."""
        self.addon = Mock()
        self.addon.api = Mock()
        self.addon.api.send_profile_hover = Mock()

    def test_load_profile_uses_send_profile_hover(self):
        """Verify load_profile uses send_profile_hover, not load_profile_by_id."""
        profile_id = "uuid-test-profile-123"

        handle_command_load_profile(self.addon, profile_id)

        # Should call send_profile_hover, not load_profile_by_id
        self.addon.api.send_profile_hover.assert_called_once()

        # Verify the method was NOT called
        self.assertFalse(
            hasattr(self.addon.api, "load_profile_by_id")
            and self.addon.api.load_profile_by_id.called
        )

    def test_load_profile_correct_payload_format(self):
        """Verify send_profile_hover receives correct payload format."""
        profile_id = "uuid-abc-def-123"

        handle_command_load_profile(self.addon, profile_id)

        # Get the actual call arguments
        call_args = self.addon.api.send_profile_hover.call_args[0][0]

        # Verify payload structure matches Socket.IO profileHover format
        self.assertIsInstance(call_args, dict)
        self.assertEqual(call_args["id"], profile_id)
        self.assertEqual(call_args["from"], "app")
        self.assertEqual(call_args["type"], "focus")

    def test_load_profile_with_various_profile_ids(self):
        """Test load_profile with different profile ID formats."""
        test_ids = [
            "simple-id",
            "uuid-1234-5678-abcd-efgh",
            "Profile Name With Spaces",
            "special_chars-123!@#",
        ]

        for profile_id in test_ids:
            self.addon.api.send_profile_hover.reset_mock()

            handle_command_load_profile(self.addon, profile_id)

            call_args = self.addon.api.send_profile_hover.call_args[0][0]
            self.assertEqual(call_args["id"], profile_id)

    def test_load_profile_no_api_connection(self):
        """Test load_profile gracefully handles missing API."""
        self.addon.api = None

        # Should not raise exception
        try:
            handle_command_load_profile(self.addon, "test-id")
        except Exception as e:
            self.fail(f"Should handle missing API gracefully: {e}")

    def test_load_profile_empty_id(self):
        """Test load_profile with empty profile ID."""
        handle_command_load_profile(self.addon, "")

        # Should not call the API
        self.addon.api.send_profile_hover.assert_not_called()

    def test_load_profile_none_id(self):
        """Test load_profile with None profile ID."""
        # Should not raise exception, just skip
        try:
            handle_command_load_profile(self.addon, None)
        except Exception as e:
            self.fail(f"Should handle None gracefully: {e}")

        self.addon.api.send_profile_hover.assert_not_called()


class TestAPIWrapperUsage(unittest.TestCase):
    """Test that addon uses pymeticulous wrappers instead of direct session calls."""

    def test_no_direct_session_calls_in_mqtt_commands(self):
        """Verify mqtt_commands.py doesn't use api.session.get/post directly."""
        mqtt_commands_path = os.path.join(
            os.path.dirname(__file__), "..", "rootfs", "usr", "bin", "mqtt_commands.py"
        )

        with open(mqtt_commands_path, "r") as f:
            content = f.read()

        # Check for direct session usage (should not exist)
        self.assertNotIn(
            "api.session.get",
            content,
            "mqtt_commands should use API wrappers, not direct session calls",
        )
        self.assertNotIn(
            "api.session.post",
            content,
            "mqtt_commands should use API wrappers, not direct session calls",
        )

    def test_run_py_uses_wrappers_for_profiles(self):
        """Verify run.py uses list_profiles() wrapper."""
        run_py_path = os.path.join(
            os.path.dirname(__file__), "..", "rootfs", "usr", "bin", "run.py"
        )

        with open(run_py_path, "r") as f:
            content = f.read()

        # Should use api.list_profiles() wrapper
        self.assertIn(
            "api.list_profiles()", content, "run.py should use api.list_profiles() wrapper"
        )

        # Should use api.get_last_profile() wrapper
        self.assertIn(
            "api.get_last_profile()", content, "run.py should use api.get_last_profile() wrapper"
        )


if __name__ == "__main__":
    unittest.main()
"""Tests for pymeticulous 0.3.0 compatibility updates."""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock

from meticulous.api_types import APIError

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "usr", "bin"))

# pyright: reportMissingImports=false
from mqtt_commands import handle_command_load_profile  # noqa: E402  # type: ignore

if __name__ == "__main__":
    unittest.main()
