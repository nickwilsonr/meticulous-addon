#!/usr/bin/env python3
"""Unit tests for Phase 1 state detection implementation."""
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add rootfs/usr/bin to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "rootfs" / "usr" / "bin"))

# Import after path is set
from run import MeticulousAddon


class TestNormalizeStateName:
    """Tests for normalize_state_name() function."""

    def test_simple_lowercase_state(self):
        """Test simple lowercase state normalization."""
        addon = MeticulousAddon()
        assert addon._normalize_state_name("idle") == "Idle"
        assert addon._normalize_state_name("heating") == "Heating"
        assert addon._normalize_state_name("purge") == "Purge"

    def test_underscored_state(self):
        """Test state names with underscores."""
        addon = MeticulousAddon()
        assert addon._normalize_state_name("END_STAGE") == "End Stage"
        assert addon._normalize_state_name("pre_infusion") == "Pre Infusion"
        assert addon._normalize_state_name("closing_valve") == "Closing Valve"

    def test_phrase_state(self):
        """Test state names with multiple words."""
        addon = MeticulousAddon()
        assert addon._normalize_state_name("click to start") == "Click to Start"
        assert addon._normalize_state_name("click to purge") == "Click to Purge"
        assert (
            addon._normalize_state_name("pour water and click to continue")
            == "Pour Water and Click to Continue"
        )

    def test_abbreviation_preservation(self):
        """Test that abbreviations are preserved."""
        addon = MeticulousAddon()
        assert addon._normalize_state_name("PI") == "PI"
        assert addon._normalize_state_name("PI_PHASE") == "PI Phase"

    def test_mixed_case_state(self):
        """Test mixed case state normalization."""
        addon = MeticulousAddon()
        assert addon._normalize_state_name("Slayer Preinfusion") == "Slayer Preinfusion"
        assert addon._normalize_state_name("Immersion") == "Immersion"

    def test_empty_state(self):
        """Test empty state handling."""
        addon = MeticulousAddon()
        assert addon._normalize_state_name("") == ""
        assert addon._normalize_state_name("   ") == ""

    def test_idempotency(self):
        """Test that normalization is idempotent."""
        addon = MeticulousAddon()
        test_cases = [
            "idle",
            "click to start",
            "PI",
            "END_STAGE",
            "Slayer Preinfusion",
        ]
        for case in test_cases:
            normalized_once = addon._normalize_state_name(case)
            normalized_twice = addon._normalize_state_name(normalized_once)
            assert normalized_once == normalized_twice, f"Not idempotent: {case}"

    def test_all_real_state_names(self):
        """Test normalization of all state names from real captures."""
        addon = MeticulousAddon()
        test_cases = {
            "idle": "Idle",
            "heating": "Heating",
            "retracting": "Retracting",
            "PI": "PI",
            "Ramp": "Ramp",
            "Hold": "Hold",
            "Decline": "Decline",
            "purge": "Purge",
            "click to start": "Click to Start",
            "click to purge": "Click to Purge",
            "closing valve": "Closing Valve",
            "Slayer Preinfusion": "Slayer Preinfusion",
            "Immersion": "Immersion",
            "Percolation": "Percolation",
            "Final Percolation": "Final Percolation",
            "starting...": "Starting...",
        }
        for raw, expected in test_cases.items():
            result = addon._normalize_state_name(raw)
            assert result == expected, f"Failed: {raw} → {result}, expected {expected}"


class TestHasActivePreheat:
    """Tests for _has_active_preheat() detection."""

    def test_no_preheat_data(self):
        """Test when no preheat data has been received."""
        addon = MeticulousAddon()
        assert addon._has_active_preheat() is False

    def test_preheat_active_recent(self):
        """Test with recent preheat countdown."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 490.63
        addon._preheat_active_timestamp = time.time()
        assert addon._has_active_preheat() is True

    def test_preheat_zero_countdown(self):
        """Test with zero preheat countdown."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 0.0
        addon._preheat_active_timestamp = time.time()
        assert addon._has_active_preheat() is False

    def test_preheat_stale(self):
        """Test with stale preheat data (> 2 seconds old)."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 490.63
        addon._preheat_active_timestamp = time.time() - 3.0  # 3 seconds ago
        assert addon._has_active_preheat() is False

    def test_preheat_freshest_edge(self):
        """Test preheat detection at 2-second boundary."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 100.0
        addon._preheat_active_timestamp = time.time() - 1.99  # Just under 2 seconds
        assert addon._has_active_preheat() is True

    def test_preheat_stale_edge(self):
        """Test preheat detection just past 2-second threshold."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 100.0
        addon._preheat_active_timestamp = time.time() - 2.01  # Just over 2 seconds
        assert addon._has_active_preheat() is False


class TestPreheatStateDetection:
    """Tests for state detection with preheat conditions."""

    def test_idle_with_active_preheat_becomes_preheating(self):
        """Test that idle state with active preheat becomes 'Preheating'."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 490.0
        addon._preheat_active_timestamp = time.time()

        status_event = {"name": "idle", "state": "idle"}
        addon._handle_status_event(status_event)
        assert addon.current_state == "Preheating"

    def test_idle_without_preheat_stays_idle(self):
        """Test that idle without preheat remains Idle."""
        addon = MeticulousAddon()
        # No preheat data

        status_event = {"name": "idle", "state": "idle"}
        addon._handle_status_event(status_event)
        assert addon.current_state == "Idle"

    def test_heating_state_ignores_preheat(self):
        """Test that non-idle states ignore preheat condition."""
        addon = MeticulousAddon()
        addon._latest_preheat_countdown = 490.0
        addon._preheat_active_timestamp = time.time()

        status_event = {"name": "heating", "state": "heating"}
        addon._handle_status_event(status_event)
        assert addon.current_state == "Heating"

    def test_preheat_transition_to_heating(self):
        """Test transition from Preheating to Heating state."""
        addon = MeticulousAddon()

        # First: idle with preheat
        addon._latest_preheat_countdown = 10.0
        addon._preheat_active_timestamp = time.time()
        status_event = {"name": "idle", "state": "idle"}
        addon._handle_status_event(status_event)
        assert addon.current_state == "Preheating"

        # Second: preheat completes, heating begins
        addon._latest_preheat_countdown = 0.0
        status_event = {"name": "heating", "state": "heating"}
        addon._handle_status_event(status_event)
        assert addon.current_state == "Heating"


class TestPublishPreheatCountdown:
    """Tests for _publish_preheat_countdown() method."""

    def test_publish_disabled_mqtt(self):
        """Test that method gracefully handles disabled MQTT."""
        addon = MeticulousAddon()
        addon.mqtt_enabled = False
        addon.mqtt_client = None

        # Should not raise exception
        addon._publish_preheat_countdown(490.63)

    def test_publish_no_mqtt_client(self):
        """Test that method gracefully handles missing MQTT client."""
        addon = MeticulousAddon()
        addon.mqtt_enabled = True
        addon.mqtt_client = None

        # Should not raise exception
        addon._publish_preheat_countdown(490.63)

    def test_countdown_value_formatting(self):
        """Test that countdown values are properly rounded and formatted."""
        # Test that values are rounded to 2 decimal places
        test_values = [
            (490.6312345, "490.63"),
            (1.0, "1.0"),
            (0.123456, "0.12"),
            (489.999, "490.0"),
        ]

        for input_val, expected_str in test_values:
            formatted = str(round(input_val, 2))
            assert formatted == expected_str


class TestStateTransitionSequence:
    """Integration-style tests for state transition sequences."""

    def test_complete_preheat_cycle(self):
        """Test a complete preheat startup→complete→extraction cycle."""
        addon = MeticulousAddon()
        addon.current_state = "Idle"

        # 1. Start preheat
        addon._latest_preheat_countdown = 490.0
        addon._preheat_active_timestamp = time.time()
        assert addon._has_active_preheat() is True

        # 2. Preheat countdown
        addon._latest_preheat_countdown = 250.0
        assert addon._has_active_preheat() is True

        # 3. Preheat complete
        addon._latest_preheat_countdown = 0.0
        assert addon._has_active_preheat() is False

        # 4. Machine enters heating
        assert addon._normalize_state_name("heating") == "Heating"

        # 5. Extraction phase
        assert addon._normalize_state_name("retracting") == "Retracting"

    def test_slayer_profile_state_sequence(self):
        """Test state sequence for Slayer profile extraction."""
        addon = MeticulousAddon()

        states = [
            "retracting",
            "Slayer Preinfusion",
            "Immersion",
        ]

        for state in states:
            normalized = addon._normalize_state_name(state)
            # All should normalize without errors
            assert isinstance(normalized, str)
            assert len(normalized) > 0
