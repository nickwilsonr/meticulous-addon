"""Integration tests for the Meticulous Espresso Add-on."""

import json
import os
import sys
import unittest
from unittest.mock import patch

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "usr", "bin"))


# These imports will show as unresolved but work at runtime
# due to dynamic path manipulation above
# pyright: reportMissingImports=false


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading."""

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_load_config_from_options_json(self, mock_open, mock_exists):
        """Test loading config from /data/options.json."""
        mock_exists.return_value = True
        test_config = {"machine_ip": "192.168.1.100", "scan_interval": 30, "log_level": "info"}
        mock_read = mock_open.return_value.__enter__.return_value.read
        mock_read.return_value = json.dumps(test_config)

        from run import MeticulousAddon

        addon = MeticulousAddon()

        self.assertEqual(addon.machine_ip, "192.168.1.100")
        self.assertEqual(addon.scan_interval, 30)

    @patch("os.path.exists")
    def test_load_config_defaults(self, mock_exists):
        """Test default config values when no file exists."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()

        # Should have default values
        self.assertEqual(addon.scan_interval, 30)
        self.assertTrue(addon.mqtt_enabled)
        self.assertEqual(addon.mqtt_host, "core-mosquitto")
        self.assertEqual(addon.mqtt_port, 1883)


class TestRetryLogic(unittest.TestCase):
    """Test exponential backoff and retry logic."""

    @patch("os.path.exists")
    def test_backoff_calculation_no_jitter(self, mock_exists):
        """Test backoff delay calculation without jitter."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()
        addon.retry_jitter = False
        addon.retry_initial = 2
        addon.retry_max = 60

        # Test exponential backoff
        self.assertEqual(addon._calculate_backoff(0), 2)
        self.assertEqual(addon._calculate_backoff(1), 4)
        self.assertEqual(addon._calculate_backoff(2), 8)
        self.assertEqual(addon._calculate_backoff(3), 16)
        self.assertEqual(addon._calculate_backoff(4), 32)
        # Should cap at max
        self.assertEqual(addon._calculate_backoff(5), 60)
        # Should stay at max
        self.assertEqual(addon._calculate_backoff(10), 60)

    @patch("os.path.exists")
    def test_backoff_calculation_with_jitter(self, mock_exists):
        """Test backoff delay calculation with jitter."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()
        addon.retry_jitter = True
        addon.retry_initial = 2
        addon.retry_max = 60

        # With jitter, delay should be within 80-120% of base
        for attempt in range(5):
            delay = addon._calculate_backoff(attempt)
            base = min(addon.retry_initial * (2**attempt), addon.retry_max)
            self.assertGreaterEqual(delay, base * 0.8)
            self.assertLessEqual(delay, base * 1.2)


class TestMQTTDiscovery(unittest.TestCase):
    """Test MQTT discovery message generation."""

    @patch("os.path.exists")
    def test_sensor_discovery_payload(self, mock_exists):
        """Test MQTT discovery payload for sensors."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()
        addon.machine_ip = "192.168.1.100"

        # Test discovery payload generation
        payload = addon._create_sensor_discovery("state", "State", "mdi:coffee-maker")

        self.assertIsInstance(payload, dict)
        self.assertIn("name", payload)
        self.assertIn("state_topic", payload)
        self.assertIn("unique_id", payload)
        self.assertIn("device", payload)
        self.assertEqual(payload["name"], "State")
        self.assertEqual(payload["icon"], "mdi:coffee-maker")

    @patch("os.path.exists")
    def test_switch_discovery_payload(self, mock_exists):
        """Test MQTT discovery payload for switches."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()

        payload = addon._create_switch_discovery(
            "sounds_enabled", "Sounds Enabled", "enable_sounds"
        )

        self.assertIsInstance(payload, dict)
        self.assertIn("command_topic", payload)
        self.assertIn("state_topic", payload)
        self.assertTrue(payload["command_topic"].endswith("/enable_sounds"))


class TestAPIConnection(unittest.TestCase):
    """Test API connection management."""

    @patch("os.path.exists")
    def test_api_initialization(self, mock_exists):
        """Test API client initialization."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()
        addon.machine_ip = "192.168.1.100"

        # API should be initialized with correct host
        self.assertIsNone(addon.api)  # Not connected yet


class TestHealthMetrics(unittest.TestCase):
    """Test health metrics tracking."""

    @patch("os.path.exists")
    def test_reconnect_counting(self, mock_exists):
        """Test reconnect counter increments."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()

        self.assertEqual(addon.reconnect_count, 0)

        # Simulate reconnects
        addon.reconnect_count += 1
        self.assertEqual(addon.reconnect_count, 1)

    @patch("os.path.exists")
    def test_error_tracking(self, mock_exists):
        """Test error tracking."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()

        self.assertIsNone(addon.last_error)
        self.assertIsNone(addon.last_error_time)


class TestStateManagement(unittest.TestCase):
    """Test state management."""

    @patch("os.path.exists")
    def test_initial_state(self, mock_exists):
        """Test initial state values."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()

        self.assertEqual(addon.current_state, "unknown")
        self.assertIsNone(addon.current_profile)
        self.assertFalse(addon.socket_connected)
        self.assertFalse(addon.api_connected)

    @patch("os.path.exists")
    def test_availability_topic(self, mock_exists):
        """Test availability topic format."""
        mock_exists.return_value = False

        from run import MeticulousAddon

        addon = MeticulousAddon()

        expected = "meticulous_espresso/availability"
        self.assertEqual(addon.availability_topic, expected)


class TestImportHandling(unittest.TestCase):
    """Test import error handling."""

    def test_pymeticulous_import(self):
        """Test pyMeticulous import succeeds."""
        try:
            from meticulous.api import Api, ApiOptions  # noqa: F401
            from meticulous.api_types import ActionType, StatusData, Temperatures  # noqa: F401
        except ImportError as e:
            self.fail(f"pyMeticulous import failed: {e}")

    def test_mqtt_import(self):
        """Test paho-mqtt import succeeds."""
        try:
            import paho.mqtt.client as mqtt  # noqa: F401
        except ImportError as e:
            self.fail(f"paho-mqtt import failed: {e}")


if __name__ == "__main__":
    unittest.main()
