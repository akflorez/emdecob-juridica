
from backend.db import SessionLocal
from backend.models import User

def check():
    db = SessionLocal()
    u = db.query(User).filter(User.username == "admin").first()
    if u:
        print(f"Admin User: ID={u.id}, Username={u.username}")
    else:
        print("Admin user not found in DB")
    db.close()

if __name__ == "__main__":
    check()
