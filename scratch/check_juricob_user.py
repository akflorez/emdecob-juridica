
from backend.db import SessionLocal
from backend.models import User

def check():
    db = SessionLocal()
    u = db.query(User).filter(User.username == "juricob").first()
    if u:
        print(f"User 'juricob' found in DB: ID={u.id}")
    else:
        print("User 'juricob' NOT found in DB")
    
    u2 = db.query(User).filter(User.id == 2).first()
    if u2:
        print(f"User ID 2 in DB: Username={u2.username}")
    else:
        print("User ID 2 NOT found in DB")
    db.close()

if __name__ == "__main__":
    check()
