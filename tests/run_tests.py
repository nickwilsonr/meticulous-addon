"""Test runner script for Meticulous Espresso Add-on."""

import builtins
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import aiohttp
import requests

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "usr", "bin"))

# Patch open, os.path.exists, requests, and aiohttp.ClientSession globally
patches = [
    patch("builtins.open", new_callable=MagicMock),
    patch("os.path.exists", return_value=False),
    patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: {})),
    patch("requests.post", return_value=MagicMock(status_code=200, json=lambda: {})),
    patch("aiohttp.ClientSession", new=MagicMock),
]
for p in patches:
    p.start()


def stop_all_patches():
    for p in patches:
        p.stop()


import atexit

atexit.register(stop_all_patches)


# Discover and run all tests in integration/ and unit/ only
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for subfolder in ["integration", "unit"]:
    test_dir = os.path.join(os.path.dirname(__file__), subfolder)
    if os.path.isdir(test_dir):
        suite.addTests(loader.discover(test_dir, pattern="test_*.py"))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with appropriate code
sys.exit(0 if result.wasSuccessful() else 1)
