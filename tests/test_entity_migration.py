"""Tests for MQTT entity migration on addon version changes."""

import asyncio
import json
import unittest
from unittest.mock import MagicMock, patch

# Test configuration
TEST_SLUG = "meticulous_espresso"
TEST_COMMAND_PREFIX = f"{TEST_SLUG}/command"
TEST_DISCOVERY_PREFIX = "homeassistant"


class TestVersionComparison(unittest.TestCase):
    """Test semantic version comparison."""

    def test_version_less_than_operator(self):
        """Test _version_less_than method correctly compares versions."""
        from rootfs.usr.bin.run import MeticulousAddon

        addon = MeticulousAddon()

        # Test less than
        self.assertTrue(addon._version_less_than("0.27.0", "0.28.0"))
        self.assertTrue(addon._version_less_than("0.27.5", "0.28.0"))
        self.assertTrue(addon._version_less_than("0.28.0", "0.28.1"))

        # Test not less than
        self.assertFalse(addon._version_less_than("0.28.0", "0.28.0"))
        self.assertFalse(addon._version_less_than("0.29.0", "0.28.0"))
        self.assertFalse(addon._version_less_than("0.28.1", "0.28.0"))

    def test_version_invalid_versions(self):
        """Test version comparison with invalid versions."""
        from rootfs.usr.bin.run import MeticulousAddon

        addon = MeticulousAddon()

        # Invalid versions should return False gracefully
        self.assertFalse(addon._version_less_than("invalid", "0.28.0"))
        self.assertFalse(addon._version_less_than("0.28.0", "invalid"))


class TestMigrationCleanup(unittest.TestCase):
    """Test entity cleanup during version migration."""

    @patch("paho.mqtt.client.Client")
    def test_cleanup_old_brew_entities(self, mock_mqtt):
        """Test cleanup of old brew_* entities on v0.27->v0.28 migration."""
        from rootfs.usr.bin.run import MeticulousAddon

        addon = MeticulousAddon()
        addon.mqtt_enabled = True
        addon.mqtt_client = MagicMock()
        addon.mqtt_client.is_connected.return_value = True
        addon.slug = TEST_SLUG
        addon.command_prefix = TEST_COMMAND_PREFIX
        addon.discovery_prefix = TEST_DISCOVERY_PREFIX
        addon.state_prefix = f"{TEST_SLUG}/sensor"

        # Mock previous version as 0.27.0
        with patch.object(addon, "_load_addon_state") as mock_load:
            mock_load.return_value = {"version": "0.27.0"}
            addon.addon_version = "0.28.0"

            # Mock save state
            with patch.object(addon, "_save_addon_state"):
                # Run migration (async)
                asyncio.run(addon._mqtt_cleanup_old_entity_versions())

                # Verify old brew topics were published
                calls = addon.mqtt_client.publish.call_args_list
                published_topics = [call[0][0] for call in calls]

                # Check that old brew topics were cleared
                old_topics = [
                    f"{addon.command_prefix}/start_brew",
                    f"{addon.command_prefix}/stop_brew",
                    f"{addon.command_prefix}/continue_brew",
                ]

                for old_topic in old_topics:
                    self.assertIn(old_topic, published_topics)

    @patch("paho.mqtt.client.Client")
    def test_no_cleanup_same_version(self, mock_mqtt):
        """Test no cleanup when version hasn't changed."""
        from rootfs.usr.bin.run import MeticulousAddon

        addon = MeticulousAddon()
        addon.mqtt_enabled = True
        addon.mqtt_client = MagicMock()

        # Mock current version already stored
        with patch.object(addon, "_load_addon_state") as mock_load:
            mock_load.return_value = {"version": "0.28.0"}
            addon.addon_version = "0.28.0"

            # Run migration
            asyncio.run(addon._mqtt_cleanup_old_entity_versions())

            # Verify no publish calls
            addon.mqtt_client.publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
