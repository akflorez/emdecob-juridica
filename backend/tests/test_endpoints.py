import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use a file-based SQLite db to share connection state across multiple sessions/threads
DB_FILE = "test_temp.db"
if os.path.exists(DB_FILE):
    try:
        os.remove(DB_FILE)
    except:
        pass

engine = create_engine(f"sqlite:///{DB_FILE}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monkey-patch backend SessionLocal before main imports resolve
import backend.db
backend.db.SessionLocal = TestingSessionLocal

from backend.db import Base
from backend.main import app, get_current_user, require_superadmin, get_db
import backend.main
backend.main.SessionLocal = TestingSessionLocal

from backend.models import User, Company, Case, BillingTier

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override db dependency globally for these tests
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Helper fixtures for mocking users
mock_normal_user = User(
    id=10,
    company_id=1,
    username="normalkarina",
    nombre="Karina Normal User",
    is_active=True,
    is_admin=False,
    is_superadmin=False,
    role="USER",
    cases_view_scope="OWN"
)

mock_superadmin_user = User(
    id=1,
    company_id=None,
    username="superadmin",
    nombre="Super Admin User",
    is_active=True,
    is_admin=True,
    is_superadmin=True,
    role="SUPERADMIN",
    cases_view_scope="GLOBAL"
)

@pytest.fixture(autouse=True)
def setup_db_records():
    # Clean up and recreate database schema before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Insert a mock company
    comp = Company(id=1, nombre="EMDECOB LTDA", nit="12345-6", estado="activo")
    db.add(comp)
    
    # Insert a mock case
    case = Case(
        id=100,
        company_id=1,
        radicado="11001400300720180080000",
        juzgado="Juzgado 1 Civil",
        demandante="Demandante Test",
        demandado="Demandado Test",
        is_active=True
    )
    db.add(case)
    
    # Insert mock tier
    tier = BillingTier(id=1, min_cases=0, max_cases=10, price=5000.0)
    db.add(tier)
    
    db.commit()
    db.close()

# Normal user overrides
def override_get_current_user_normal():
    return mock_normal_user

def override_require_superadmin_normal():
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail="Not authorized, require SuperAdmin")

# SuperAdmin overrides
def override_get_current_user_sa():
    return mock_superadmin_user

def override_require_superadmin_sa():
    return mock_superadmin_user


# --- Tests ---

def test_auth_me_endpoint():
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "normalkarina"

def test_get_cases_endpoint():
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Normal user should see their cases (or cases in their company depending on scope)
    assert len(data["items"]) == 1
    assert data["items"][0]["radicado"] == "11001400300720180080000"

def test_get_case_detail_endpoint():
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    response = client.get("/api/cases/id/100")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 100
    assert data["radicado"] == "11001400300720180080000"

def test_get_companies_endpoint():
    app.dependency_overrides[require_superadmin] = override_require_superadmin_sa
    response = client.get("/api/admin/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nombre"] == "EMDECOB LTDA"

def test_get_users_endpoint():
    # Regular users should not access admin endpoints
    app.dependency_overrides[require_superadmin] = override_require_superadmin_normal
    response = client.get("/api/admin/users")
    assert response.status_code == 403

def test_billing_tiers_endpoint():
    app.dependency_overrides[require_superadmin] = override_require_superadmin_sa
    response = client.get("/api/admin/billing/tiers")
    assert response.status_code == 200

def test_billing_simulator_endpoint():
    app.dependency_overrides[require_superadmin] = override_require_superadmin_sa
    response = client.get("/api/admin/billing/simulator")
    assert response.status_code == 200

def test_debug_endpoint_requires_superadmin():
    # Test that normal user is rejected from debug
    app.dependency_overrides[require_superadmin] = override_require_superadmin_normal
    response = client.post("/api/admin/judicial-sources/debug", json={"radicado": "11001400300720180080000", "dry_run": True})
    assert response.status_code == 403
    
    # Test that superadmin is authorized
    app.dependency_overrides[require_superadmin] = override_require_superadmin_sa
    app.dependency_overrides[get_current_user] = override_get_current_user_sa
    response = client.post("/api/admin/judicial-sources/debug", json={"radicado": "11001400300720180080000", "dry_run": True})
    assert response.status_code == 200
    data = response.json()
    assert data["radicado"] == "11001400300720180080000"
    assert len(data["sources_checked"]) == 4

def test_multisource_check_endpoints():
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    
    # Trigger check
    response = client.post("/api/cases/100/multisource-check")
    assert response.status_code == 200
    assert "encolada" in response.json()["message"]
    
    # Retrieve checks
    response = client.get("/api/cases/100/multisource-checks")
    assert response.status_code == 200

# Cleanup test file after execution
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db_file():
    yield
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except:
            pass
