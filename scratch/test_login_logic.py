import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.db import SessionLocal
from backend.models import User
from sqlalchemy import or_

def test_login(username, password):
    db = SessionLocal()
    user_db = db.query(User).filter(
        or_(User.username == username, User.email == username),
        User.is_active == True
    ).first()
    
    if not user_db:
        print(f"User {username} not found in DB!")
        return
        
    print(f"Found user_db: {user_db.username}, hash: {user_db.hashed_password}")
    
    from backend.main import _verify_password
    res = _verify_password(password, user_db.hashed_password)
    print(f"Verify result: {res}")

if __name__ == "__main__":
    test_login("akflorez", "Emdecob2026*")
