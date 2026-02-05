"""Pytest configuration and fixtures for unit tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add rootfs/usr/bin to Python path
rootfs_path = Path(__file__).parent.parent.parent / "rootfs" / "usr" / "bin"
sys.path.insert(0, str(rootfs_path))

# Mock mqtt_commands before importing run.py
sys.modules["mqtt_commands"] = MagicMock()
