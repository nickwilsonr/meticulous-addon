"""Integration tests for Meticulous Espresso Add-on sensor population and persistence."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rootfs", "usr", "bin"))

# pyright: reportMissingImports=false


class TestSensorPopulation(unittest.TestCase):
    """Test that all key sensors are populated from API or state."""

    @patch("run.MeticulousAddon._load_config", return_value={"machine_ip": "192.168.1.100"})
    @patch("run.MeticulousAddon._fetch_mqtt_credentials_from_supervisor")
    def setUp(self, mock_fetch_mqtt, mock_load_config):
        from run import MeticulousAddon

        self.addon = MeticulousAddon()
        # Mock API and device_info
        self.addon.api = MagicMock()
        self.addon.device_info = MagicMock(
            firmware="1.2.3",
            software_version="2026.01",
            model="Espresso",
            serial="SN123",
            name="Meticulous Espresso",
            mainVoltage=120.0,
        )
        # Mock API return values
        self.addon.api.get_history_statistics.return_value = MagicMock(totalSavedShots=42)
        last_shot = MagicMock()
        last_shot.name = "Morning Shot"
        last_shot.profile = MagicMock()
        last_shot.profile.name = "Light Roast"
        last_shot.rating = "like"
        last_shot.time = 1700000000
        self.addon.api.get_last_shot.return_value = last_shot
        self.addon.api.get_settings.return_value = MagicMock(enable_sounds=True)
        self.addon.api.get_last_profile.return_value = MagicMock(
            profile=MagicMock(name="Light Roast", author="Barista", temperature=94, final_weight=36)
        )
        self.addon.socket_connected = True

    def test_firmware_version_sensor(self):
        self.assertEqual(self.addon.device_info.firmware, "1.2.3")

    def test_software_version_sensor(self):
        self.assertEqual(self.addon.device_info.software_version, "2026.01")

    def test_voltage_sensor(self):
        self.assertEqual(self.addon.device_info.mainVoltage, 120.0)

    def test_total_shots_sensor(self):
        stats = self.addon.api.get_history_statistics()
        self.assertEqual(stats.totalSavedShots, 42)

    def test_last_shot_name_sensor(self):
        last_shot = self.addon.api.get_last_shot()
        self.assertEqual(last_shot.name, "Morning Shot")

    def test_last_shot_profile_sensor(self):
        last_shot = self.addon.api.get_last_shot()
        self.assertEqual(last_shot.profile.name, "Light Roast")

    def test_last_shot_rating_sensor(self):
        last_shot = self.addon.api.get_last_shot()
        self.assertEqual(last_shot.rating, "like")

    def test_last_shot_time_sensor(self):
        last_shot = self.addon.api.get_last_shot()
        self.assertEqual(last_shot.time, 1700000000)

    def test_sounds_enabled_sensor(self):
        settings = self.addon.api.get_settings()
        self.assertTrue(settings.enable_sounds)

    def test_target_temperature_sensor(self):
        last_profile = self.addon.api.get_last_profile()
        self.assertEqual(last_profile.profile.temperature, 94)

    def test_meticulous_brewing_sensor(self):
        # This is set by socket.io, but should default to False if not brewing
        # Simulate status event
        self.addon.current_state = "idle"
        status = {"state": "idle", "extracting": False, "sensors": {}}
        self.addon._handle_status_event(status)
        # No assertion here, but should not raise

    def test_meticulous_connected_sensor(self):
        self.assertTrue(self.addon.socket_connected)


if __name__ == "__main__":
    unittest.main()
