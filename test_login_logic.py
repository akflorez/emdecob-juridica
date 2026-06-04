import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from backend.main import _verify_password, SessionLocal
from backend.models import User

db = SessionLocal()
user_db = db.query(User).filter(User.username == "superadmin").first()

if user_db:
    print("Hash from DB:", user_db.hashed_password)
    print("Match:", _verify_password("admin123$", user_db.hashed_password))
    print("User is_active:", user_db.is_active)
else:
    print("User not found.")
