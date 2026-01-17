#!/usr/bin/env python3
"""Inspect the send_profile_hover method."""

import inspect
from pymeticulous.client import APIClient

# Get the method
method = getattr(APIClient, 'send_profile_hover', None)
if method:
    source = inspect.getsource(method)
    print("Method source:")
    print(source)
else:
    print("send_profile_hover method not found")
    print("\nAvailable methods containing 'profile':")
    methods = [m for m in dir(APIClient) if 'profile' in m.lower() and not m.startswith('_')]
    for m in methods:
        print(f"  - {m}")
