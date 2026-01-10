#!/usr/bin/env python3
"""Quick test of the profiles endpoint."""
from meticulous.api import Api
import json

# Create API connection
api = Api(base_url="http://192.168.0.115:8080/")

# Test machine endpoint first (known to work)
print("=" * 60)
print("Testing /api/v1/machine (known endpoint)")
print("=" * 60)
try:
    url = f"{api.base_url.rstrip('/')}/api/v1/machine"
    print(f"URL: {url}")
    resp = api.session.get(url)
    resp.raise_for_status()
    data = resp.json()
    print("✓ SUCCESS!")
    print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"✗ Failed: {e}")

# Try profile endpoints
print("\n" + "=" * 60)
print("Testing profile endpoints")
print("=" * 60)
for endpoint in ["api/v1/profiles", "api/v1/profile", "api/v1/profiles/available"]:
    try:
        url = f"{api.base_url.rstrip('/')}/{endpoint}"
        print(f"\n{endpoint}:")
        resp = api.session.get(url, timeout=2)
        resp.raise_for_status()
        data = resp.json()
        print(f"  ✓ SUCCESS! Got payload:")
        print(f"  {json.dumps(data, indent=2)[:300]}")
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {e}")
