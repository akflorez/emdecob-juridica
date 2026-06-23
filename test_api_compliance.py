import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add current dir to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.main import app, create_access_token, is_global_superadmin
from backend.db import SessionLocal
from backend.models import User, Company, BillingTier, AuditLog

client = TestClient(app)

def run_tests():
    db: Session = SessionLocal()
    print("=== STARTING API COMPLIANCE TESTS ===")

    # 1. Ensure we have a SuperAdmin
    superadmin = db.query(User).filter((User.role == "SUPERADMIN") | (User.is_superadmin == True), User.is_active == True).first()
    if not superadmin:
        print("[TEST] Creating temporary test SuperAdmin...")
        superadmin = User(
            username="test_superadmin_compliance",
            nombre="SuperAdmin de Prueba",
            role="SUPERADMIN",
            cases_view_scope="GLOBAL",
            is_superadmin=True,
            is_admin=True,
            is_active=True,
            hashed_password="not_used_directly"
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
    else:
        print(f"[TEST] Found existing SuperAdmin: {superadmin.username}")

    # Generate token
    sa_token = create_access_token(superadmin.id)
    headers = {"Authorization": f"Bearer {sa_token}"}

    # 2. Test GET /api/auth/me
    print("\n1. Testing GET /api/auth/me ...")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print("[OK] /api/auth/me returned 200")
    print("[INFO] Response:", data)
    assert data["role"] == "SUPERADMIN"
    assert data["cases_view_scope"] == "GLOBAL"
    assert data["is_superadmin"] is True
    assert data["is_active"] is True
    assert "permissions" in data

    # 3. Test GET /api/admin/companies
    print("\n2. Testing GET /api/admin/companies ...")
    res = client.get("/api/admin/companies", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print(f"[OK] GET /api/admin/companies returned 200. Total companies: {len(res.json())}")

    # 4. Test GET /api/admin/users
    print("\n3. Testing GET /api/admin/users ...")
    res = client.get("/api/admin/users", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print(f"[OK] GET /api/admin/users returned 200. Total users: {len(res.json())}")

    # 5. Test GET /api/admin/billing/tiers
    print("\n4. Testing GET /api/admin/billing/tiers ...")
    res = client.get("/api/admin/billing/tiers", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print(f"[OK] GET /api/admin/billing/tiers returned 200")

    # 6. Test GET /api/admin/billing/simulator
    print("\n5. Testing GET /api/admin/billing/simulator ...")
    res = client.get("/api/admin/billing/simulator", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    sim_data = res.json()
    print(f"[OK] GET /api/admin/billing/simulator returned 200")
    print(f"[INFO] Tiers count: {len(sim_data.get('tiers', []))}")
    print(f"[INFO] Summary: {sim_data.get('summary')}")

    # 7. Test lockout prevention (SuperAdmin self-deactivation)
    print("\n6. Testing lockout protection: SuperAdmin cannot deactivate self ...")
    payload = {"is_active": False}
    res = client.put(f"/api/admin/users/{superadmin.id}", json=payload, headers=headers)
    assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
    print(f"[OK] Self-deactivation blocked correctly: {res.json()}")

    # 8. Test lockout prevention: SuperAdmin cannot demote self
    print("\n7. Testing lockout protection: SuperAdmin cannot demote self ...")
    payload = {"role": "USER", "cases_view_scope": "OWN"}
    res = client.put(f"/api/admin/users/{superadmin.id}", json=payload, headers=headers)
    assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
    print(f"[OK] Self-demotion blocked correctly: {res.json()}")

    # 9. Test scope validation
    print("\n8. Testing cases_view_scope validations ...")
    # Try to set GLOBAL scope on a non-superadmin (or create a standard user with GLOBAL)
    test_user_payload = {
        "username": "compliance_test_user_std",
        "password": "some_test_password",
        "nombre": "User Estandar Prueba",
        "role": "USER",
        "cases_view_scope": "GLOBAL",
        "company_id": 1, # assuming company id 1 exists, let's retrieve or use a valid one
        "email": "std@compliance.com"
    }
    # Let's get a valid company id first
    comp = db.query(Company).first()
    if not comp:
        # Create temp company
        print("[TEST] Creating temporary company...")
        comp = Company(nombre="Temp Compliance Company", nit="123", estado="activo")
        db.add(comp)
        db.commit()
        db.refresh(comp)
    test_user_payload["company_id"] = comp.id

    res = client.post("/api/admin/users", json=test_user_payload, headers=headers)
    assert res.status_code == 400, f"Expected 400 for standard user with GLOBAL scope, got {res.status_code}"
    print(f"[OK] Assigning GLOBAL to standard user blocked correctly: {res.json()['detail']}")

    # 10. Test Company Admin restrictions
    # Let's create a Company Admin
    company_admin = db.query(User).filter(User.role == "COMPANY_ADMIN", User.company_id == comp.id).first()
    if not company_admin:
        company_admin = User(
            username="compliance_comp_admin",
            nombre="Company Admin de Prueba",
            role="COMPANY_ADMIN",
            cases_view_scope="COMPANY",
            is_superadmin=False,
            is_admin=True,
            is_active=True,
            company_id=comp.id,
            hashed_password="not_used_directly"
        )
        db.add(company_admin)
        db.commit()
        db.refresh(company_admin)

    comp_admin_token = create_access_token(company_admin.id)
    comp_admin_headers = {"Authorization": f"Bearer {comp_admin_token}"}

    print("\n9. Testing Company Admin restrictions ...")
    # Company admin attempts to create a SUPERADMIN
    payload_sa_create = {
        "username": "compliance_should_fail_sa",
        "password": "pass",
        "nombre": "Failed SA",
        "role": "SUPERADMIN",
        "cases_view_scope": "GLOBAL",
        "company_id": None
    }
    res = client.post("/api/admin/users", json=payload_sa_create, headers=comp_admin_headers)
    assert res.status_code == 400 or res.status_code == 403, f"Expected 400/403 for company admin creating SUPERADMIN, got {res.status_code}"
    print(f"[OK] Company Admin blocked from creating SuperAdmin: {res.json()['detail']}")

    # Company admin attempts to assign user to a different company
    payload_other_comp = {
        "username": "compliance_should_fail_comp",
        "password": "pass",
        "nombre": "Failed Comp",
        "role": "USER",
        "cases_view_scope": "OWN",
        "company_id": comp.id + 9999
    }
    res = client.post("/api/admin/users", json=payload_other_comp, headers=comp_admin_headers)
    assert res.status_code == 400 or res.status_code == 403, f"Expected 400/403 for company admin assigning other company, got {res.status_code}"
    print(f"[OK] Company Admin blocked from assigning other company ID: {res.json()['detail']}")

    # 11. Test 403 Suspension logic
    print("\n10. Testing company suspension lockout ...")
    # Suspend the company
    comp.estado = "suspendida_pago"
    db.commit()

    # Create a standard active user in this suspended company
    suspended_user = db.query(User).filter(User.company_id == comp.id, User.role == "USER", User.is_active == True).first()
    if not suspended_user:
        suspended_user = User(
            username="compliance_suspended_user",
            nombre="User Suspendido",
            role="USER",
            cases_view_scope="OWN",
            is_active=True,
            company_id=comp.id,
            hashed_password="not_used_directly"
        )
        db.add(suspended_user)
        db.commit()
        db.refresh(suspended_user)

    su_token = create_access_token(suspended_user.id)
    su_headers = {"Authorization": f"Bearer {su_token}"}

    # Hitting a normal authenticated endpoint (e.g. /api/auth/me) with the suspended user's token should return 403
    res = client.get("/api/auth/me", headers=su_headers)
    assert res.status_code == 403, f"Expected 403 Forbidden for suspended company user, got {res.status_code}"
    res_data = res.json()
    print(f"[OK] Suspended company user locked out correctly with status 403. Message: {res_data['detail']}")
    assert "Tu empresa se encuentra suspendida. Por favor contacta al administrador." in res_data['detail']

    # Reactivate company
    comp.estado = "activo"
    db.commit()
    res = client.get("/api/auth/me", headers=su_headers)
    assert res.status_code == 200, f"Expected 200 after company reactivation, got {res.status_code}"
    print("[OK] Suspended user logged back in successfully after company reactivation")

    # Clean up temp test resources safely
    print("\nCleaning up temporary test resources...")
    try:
        # Delete dummy/temporary users created during this test
        db.query(User).filter(User.username.like("compliance_%")).delete(synchronize_session=False)
        db.commit()
        print("[OK] Temporary test resources cleaned up.")
    except Exception as e:
        print("[WARN] Error during cleanup:", e)

    db.close()
    print("\n=== ALL COMPLIANCE TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
