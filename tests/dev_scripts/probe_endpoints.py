#!/usr/bin/env python3
"""Probe available API endpoints."""
from meticulous.api import Api

api = Api(base_url="http://192.168.0.115:8080/")

test_endpoints = [
    "api/v1/",
    "api/v1/health",
    "api/v1/status",
    "api/v1/brew",
    "api/v1/profiles/list",
    "api/v1/profile/list",
    "api/v1/profile/current",
    "api/v1/profile/active",
    "api/v1/profile/load",
    "api/v1/history",
    "api/v1/settings",
]

print("Probing available endpoints...\n")
for ep in test_endpoints:
    try:
        url = f"{api.base_url.rstrip('/')}/{ep}"
        resp = api.session.get(url, timeout=1)
        print(f"✓ {ep:30} -> {resp.status_code}")
    except Exception as e:
        print(f"✗ {ep:30} -> {type(e).__name__}")
