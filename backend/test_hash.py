import os
import sys
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.models import User

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
db_url = os.environ.get("DATABASE_URL")
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

u = db.query(User).filter(User.username == "superadmin").first()
if u:
    print("Hash from DB:", u.hashed_password)
    ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    print("Match:", ctx.verify("admin123$", u.hashed_password))
else:
    print("User not found.")
