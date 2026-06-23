import os
import sys
import urllib.request
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import create_access_token

# User 2 is 'admin'
token = create_access_token(2)
url = "http://84.247.130.122:8090/api/admin/billing/simulator"

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

print(f"Requesting {url} as user ID 2...")
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("User-Agent", user_agent)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        print(f"STATUS: {status}")
        print(f"BODY: {body[:300]}")
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR: {e.code}")
    try:
        print(f"BODY: {e.read().decode('utf-8')}")
    except Exception:
        print("Could not read body")
except Exception as e:
    print(f"ERROR: {e}")
