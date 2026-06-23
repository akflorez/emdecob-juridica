import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app, create_access_token

client = TestClient(app)

# 1. Generate token for Superadmin: User 21 (akflorez)
sa_token = create_access_token(21)
print(f"Superadmin Token: {sa_token}\n")

# 2. Generate token for Normal User: User 22 (testuser)
normal_token = create_access_token(22)
print(f"Normal User Token: {normal_token}\n")

def test_endpoint(name, url, token, expected_status):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(url, headers=headers)
    print(f"GET {url} (expected {expected_status}) -> Got {response.status_code}")
    if response.status_code != expected_status:
        print(f"ERROR: {response.text}")
    else:
        try:
            print("Payload:", response.json())
        except Exception:
            print("Payload:", response.text[:200])
    print("-" * 50)
    return response.status_code == expected_status

print("=== TESTING AS SUPERADMIN ===")
endpoints = [
    ("/auth/me", 200),
    ("/admin/companies", 200),
    ("/admin/users", 200),
    ("/admin/billing/tiers", 200),
    ("/admin/billing/simulator", 200)
]

sa_success = True
for url, status in endpoints:
    if not test_endpoint("Superadmin", url, sa_token, status):
        sa_success = False

print("\n=== TESTING AS NORMAL USER (EXPECTING 403) ===")
normal_success = True
for url, status in endpoints:
    # /auth/me should succeed (200) but not be superadmin
    expected = 200 if url == "/auth/me" else 403
    if not test_endpoint("Normal User", url, normal_token, expected):
        normal_success = False

if sa_success and normal_success:
    print("\nALL LOCAL TESTS PASSED SUCCESSFULLY! [OK]")
    sys.exit(0)
else:
    print("\nSOME TESTS FAILED! [FAIL]")
    sys.exit(1)
