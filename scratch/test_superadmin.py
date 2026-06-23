import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Let's import the User model from backend.models
from backend.models import User

# Let's import is_global_superadmin from backend.main
from backend.main import is_global_superadmin

db = SessionLocal()
try:
    for uid in [21, 35]:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            print(f"\n--- Testing User {user.username} (ID: {user.id}) ---")
            print(f"is_admin: {user.is_admin}")
            print(f"company_id: {user.company_id}")
            
            # check getattr
            print(f"getattr(user, 'is_superadmin', False): {getattr(user, 'is_superadmin', False)}")
            print(f"getattr(user, 'role', None): {getattr(user, 'role', None)}")
            
            # call is_global_superadmin
            res = is_global_superadmin(user)
            print(f"is_global_superadmin(user): {res}")
        else:
            print(f"User ID {uid} not found")
finally:
    db.close()
