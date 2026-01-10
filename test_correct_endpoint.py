#!/usr/bin/env python3
"""Test the correct profile endpoint."""
from meticulous.api import Api
import json

api = Api(base_url="http://192.168.0.115:8080/")

url = f"{api.base_url.rstrip('/')}/api/v1/profile/list"
print(f"Testing: {url}\n")

try:
    resp = api.session.get(url)
    resp.raise_for_status()
    data = resp.json()
    print("✓ SUCCESS! Got payload:")
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"✗ Failed: {e}")
