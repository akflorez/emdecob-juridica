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

def test_download_cases_excel():
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    
    # Insert events for case 100
    db = TestingSessionLocal()
    from backend.models import CaseEvent
    
    # Event 1 (older)
    ev1 = CaseEvent(
        case_id=100,
        company_id=1,
        event_date="2024-05-01",
        title="Auto older",
        detail="Older detail description",
        event_hash="hash1"
    )
    # Event 2 (newer)
    ev2 = CaseEvent(
        case_id=100,
        company_id=1,
        event_date="2024-05-10",
        title="Auto newer",
        detail="Newer detail description that is longer than title",
        event_hash="hash2"
    )
    db.add(ev1)
    db.add(ev2)
    db.commit()
    db.close()
    
    response = client.get("/cases/download")
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]
    
    import pandas as pd
    from io import BytesIO
    df = pd.read_excel(BytesIO(response.content))
    
    assert "Descripción última actuación" in df.columns
    assert "Fecha de última actuación" in df.columns
    assert "Empresa" in df.columns
    assert "Usuario asignado" in df.columns
    
    row = df[df["Radicado"] == "11001400300720180080000"].iloc[0]
    assert row["Descripción última actuación"] == "Newer detail description that is longer than title"
    assert row["Empresa"] == "EMDECOB LTDA"


def test_password_recovery_flow():
    from backend.models import User, Company, PasswordResetToken
    from datetime import datetime, timedelta
    
    db = TestingSessionLocal()
    
    # 1. Create mock company & users
    active_company = Company(id=10, nombre="Active Company", estado="activo")
    inactive_company = Company(id=20, nombre="Inactive Company", estado="inactivo")
    db.add(active_company)
    db.add(inactive_company)
    db.flush()
    
    # Active user
    u_active = User(
        id=101,
        company_id=10,
        username="active_rec",
        email="active@emdecob.com",
        hashed_password="old_password",
        is_active=True
    )
    # Inactive user
    u_inactive = User(
        id=102,
        company_id=10,
        username="inactive_rec",
        email="inactive@emdecob.com",
        hashed_password="old_password",
        is_active=False
    )
    # User of inactive company
    u_in_comp = User(
        id=103,
        company_id=20,
        username="in_comp_rec",
        email="in_comp@emdecob.com",
        hashed_password="old_password",
        is_active=True
    )
    db.add(u_active)
    db.add(u_inactive)
    db.add(u_in_comp)
    db.commit()
    db.close()
    
    # Test 1: Non-existent email -> returns generic response, no token in DB
    resp = client.post("/auth/forgot-password", json={"email": "non_existent@emdecob.com"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    db = TestingSessionLocal()
    assert db.query(PasswordResetToken).count() == 0
    db.close()
    
    # Test 2: Inactive user -> returns generic response, no token in DB
    resp = client.post("/auth/forgot-password", json={"email": "inactive@emdecob.com"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    db = TestingSessionLocal()
    assert db.query(PasswordResetToken).count() == 0
    db.close()
    
    # Test 3: Inactive company user -> returns generic response, no token in DB
    resp = client.post("/auth/forgot-password", json={"email": "in_comp@emdecob.com"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    db = TestingSessionLocal()
    assert db.query(PasswordResetToken).count() == 0
    db.close()
    
    # Test 4: Active user -> returns generic response, creates token in DB
    from backend.main import RATE_LIMIT_STORE
    RATE_LIMIT_STORE.clear()
    
    resp = client.post("/auth/forgot-password", json={"email": "active@emdecob.com"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    db = TestingSessionLocal()
    tokens = db.query(PasswordResetToken).all()
    assert len(tokens) == 1
    assert tokens[0].user_id == 101
    assert tokens[0].used_at is None
    db.close()
    
    # Test 5: Reset password with password mismatch -> 400
    resp = client.post("/auth/reset-password", json={
        "token": "dummy_raw_token",
        "new_password": "NewPassword123!",
        "confirm_password": "DifferentPassword123!"
    })
    assert resp.status_code == 400
    assert "no coinciden" in resp.json()["detail"]
    
    # Test 6: Reset password with weak password (too short) -> 400
    resp = client.post("/auth/reset-password", json={
        "token": "dummy_raw_token",
        "new_password": "Pw1",
        "confirm_password": "Pw1"
    })
    assert resp.status_code == 400
    assert "8 caracteres" in resp.json()["detail"]
    
    # Test 7: Reset password with weak password (no number/letter) -> 400
    resp = client.post("/auth/reset-password", json={
        "token": "dummy_raw_token",
        "new_password": "onlyletters",
        "confirm_password": "onlyletters"
    })
    assert resp.status_code == 400
    assert "letra y un número" in resp.json()["detail"]
    
    # Test 8: Reset password with invalid token -> 400
    resp = client.post("/auth/reset-password", json={
        "token": "invalid_raw_token",
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    })
    assert resp.status_code == 400
    assert "expiró o ya fue usado" in resp.json()["detail"]
    
    # Test 9: Reset password with expired token -> 400
    db = TestingSessionLocal()
    # Expire the token
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == 101).update({
        PasswordResetToken.expires_at: datetime.utcnow() - timedelta(minutes=1)
    })
    db.commit()
    db.close()
    
    # Generate new valid token
    RATE_LIMIT_STORE.clear()
    resp = client.post("/auth/forgot-password", json={"email": "active@emdecob.com"})
    assert resp.status_code == 200
    
    import hashlib
    raw_tok = "thisisasecuretoken1234567890abcde"
    h = hashlib.sha256(raw_tok.encode()).hexdigest()
    
    db = TestingSessionLocal()
    db.query(PasswordResetToken).filter(PasswordResetToken.used_at.is_(None)).update({
        PasswordResetToken.token_hash: h
    })
    db.commit()
    db.close()
    
    # Test 10: Valid token -> updates password successfully, marks used
    resp = client.post("/auth/reset-password", json={
        "token": raw_tok,
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    # Test 11: Re-use same token -> 400
    resp = client.post("/auth/reset-password", json={
        "token": raw_tok,
        "new_password": "AnotherNewPassword123!",
        "confirm_password": "AnotherNewPassword123!"
    })
    assert resp.status_code == 400
    assert "expiró o ya fue usado" in resp.json()["detail"]


def test_company_registration_status_and_role():
    # Setup fresh DB state or check directly via registration endpoint
    payload = {
        "company_name": "New Test Company LLC",
        "company_nit": "999-999-999-1",
        "admin_name": "Admin Karinitas",
        "email": "adminkarinitas@testcompany.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    
    # Use normal dependencies since we bypass auth for signup
    app.dependency_overrides.clear()
    
    response = client.post("/auth/register-company", json=payload)
    assert response.status_code == 200
    
    # Verify in DB
    db = TestingSessionLocal()
    comp = db.query(Company).filter(Company.nombre == "New Test Company LLC").first()
    assert comp is not None
    assert comp.estado == "activo"  # Verify fixed string status
    
    user = db.query(User).filter(User.email == "adminkarinitas@testcompany.com").first()
    assert user is not None
    assert user.role == "COMPANY_ADMIN"
    assert user.is_admin is True
    assert user.cases_view_scope == "COMPANY"
    db.close()


def test_task_checklist_comment_company_isolation():
    from backend.models import Task, TaskChecklistItem, TaskComment, Workspace, ProjectList
    
    db = TestingSessionLocal()
    # Create two companies
    c1 = Company(id=10, nombre="Company 10", nit="10-10", estado="activo")
    c2 = Company(id=11, nombre="Company 11", nit="11-11", estado="activo")
    db.add(c1)
    db.add(c2)
    
    # Create workspace and list
    ws = Workspace(id=1, name="Workspace 1")
    plist = ProjectList(id=1, name="List 1", workspace_id=1)
    db.add(ws)
    db.add(plist)
    
    # Create cases
    case1 = Case(id=1001, company_id=10, radicado="1001001001", demandante="C1 Demandante", is_active=True)
    case2 = Case(id=1002, company_id=11, radicado="1002002002", demandante="C2 Demandante", is_active=True)
    db.add(case1)
    db.add(case2)
    
    # Create tasks
    task1 = Task(id=501, company_id=10, case_id=1001, list_id=1, title="Task 1 Company 10", status="ABIERTO")
    task2 = Task(id=502, company_id=11, case_id=1002, list_id=1, title="Task 2 Company 11", status="ABIERTO")
    db.add(task1)
    db.add(task2)
    
    # Create checklists and comments
    chk1 = TaskChecklistItem(id=901, task_id=501, content="Checklist 1 Task 1", is_completed=False)
    comment1 = TaskComment(id=801, task_id=501, user_id=10, content="Comment 1 Task 1")
    db.add(chk1)
    db.add(comment1)
    
    db.commit()
    db.close()

    # Define mock users representing different actors
    user_c1 = User(id=10, company_id=10, username="user_c1", nombre="User C1", is_active=True, is_admin=False, role="USER", cases_view_scope="OWN")
    user_c2 = User(id=11, company_id=11, username="user_c2", nombre="User C2", is_active=True, is_admin=False, role="USER", cases_view_scope="OWN")
    sa = User(id=1, company_id=None, username="sa", nombre="Super Admin", is_active=True, is_admin=True, is_superadmin=True, role="SUPERADMIN", cases_view_scope="GLOBAL")

    # 1. Test update Task
    # Actor 1: User from company 1 updates task 1 -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: user_c1
    resp = client.patch("/api/tasks/501", json={"title": "Updated Task 1"})
    assert resp.status_code == 200

    # Actor 2: User from company 2 updates task 1 -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: user_c2
    resp = client.patch("/api/tasks/501", json={"title": "Hack Task 1"})
    assert resp.status_code == 403

    # Actor 3: SuperAdmin updates task 1 -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: sa
    resp = client.patch("/api/tasks/501", json={"title": "SA Task 1"})
    assert resp.status_code == 200

    # 2. Test update Task Checklist Item
    # Actor 1: User from company 1 updates checklist 1 -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: user_c1
    resp = client.patch("/api/tasks/checklists/901", json={"is_completed": True})
    assert resp.status_code == 200

    # Actor 2: User from company 2 updates checklist 1 -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: user_c2
    resp = client.patch("/api/tasks/checklists/901", json={"is_completed": True})
    assert resp.status_code == 403

    # Actor 3: SuperAdmin updates checklist 1 -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: sa
    resp = client.patch("/api/tasks/checklists/901", json={"is_completed": False})
    assert resp.status_code == 200

    # 3. Test update Task Comment
    # Actor 1: User from company 1 updates comment 1 -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: user_c1
    resp = client.patch("/api/tasks/comments/801", json={"content": "Updated comment by user 1"})
    assert resp.status_code == 200

    # Actor 2: User from company 2 updates comment 1 -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: user_c2
    resp = client.patch("/api/tasks/comments/801", json={"content": "Hacked comment"})
    assert resp.status_code == 403

    # Actor 3: SuperAdmin updates comment 1 -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: sa
    resp = client.patch("/api/tasks/comments/801", json={"content": "SA comment"})
    assert resp.status_code == 200



# Cleanup test file after execution
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db_file():
    yield
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except:
            pass
