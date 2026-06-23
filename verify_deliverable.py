import asyncio
import httpx
from bs4 import BeautifulSoup

from backend.db import SessionLocal
from backend.models import User, Company, CasePublication, Case, CasePublicationSearch
from backend.main import app

from fastapi.testclient import TestClient

client = TestClient(app)

def get_auth_headers(db_session, email):
    # Find user and return an override token (for test client we might just generate a token)
    # Actually, we can use the login endpoint to get a token!
    from backend.main import create_access_token
    from datetime import timedelta
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        return {}
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}

def run_tests():
    db = SessionLocal()
    
    # Let's get superadmin email and a normal user email
    sa = db.query(User).filter(User.role == "SuperAdmin").first()
    normal_user = db.query(User).filter(User.role != "SuperAdmin").first()
    
    sa_headers = get_auth_headers(db, sa.email) if sa else {}
    user_headers = get_auth_headers(db, normal_user.email) if normal_user else {}
    
    print("\n--- TEST: Endpoint GET /cases/{radicado}/publicaciones for POSITIVE CASE ---")
    pos_radicado = "11001400302420240140300"
    
    print("\n[As Normal User]")
    resp = client.get(f"/cases/{pos_radicado}/publicaciones", headers=user_headers)
    print("Status:", resp.status_code)
    try:
        data = resp.json()
        print("Fields in first publication:", list(data[0].keys()) if data else "No publications")
        if data and 'match_score' in data[0]:
            print("ERROR: Technical fields visible to normal user!")
        else:
            print("SUCCESS: Technical fields hidden from normal user.")
    except Exception as e:
        print("Error parsing JSON", e)

    print("\n[As SuperAdmin]")
    resp = client.get(f"/cases/{pos_radicado}/publicaciones", headers=sa_headers)
    print("Status:", resp.status_code)
    try:
        data = resp.json()
        print("Fields in first publication:", list(data[0].keys()) if data else "No publications")
        if data and 'match_score' in data[0]:
            print("SUCCESS: Technical fields visible to SuperAdmin.")
        else:
            print("ERROR: Technical fields hidden from SuperAdmin!")
    except Exception as e:
        print("Error parsing JSON", e)

    db.close()

if __name__ == "__main__":
    run_tests()
