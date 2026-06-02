import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.main import _hash_password
from backend.models import User
from dotenv import load_dotenv

def fix_superadmin():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    db_url = os.environ.get("DATABASE_URL")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    u = db.query(User).filter(User.username == "superadmin").first()
    if u:
        u.hashed_password = _hash_password("admin123$")
        db.commit()
        print("Superadmin password updated with correct hash.")
    else:
        print("Superadmin not found.")

if __name__ == "__main__":
    fix_superadmin()
