
from backend.db import SessionLocal
from backend.models import User, Case

def check():
    db = SessionLocal()
    users = db.query(User).all()
    print("ALL USERS with 'juri' or ID 2:")
    for u in users:
        uname = u.username.lower()
        if "juri" in uname or u.id == 2:
            case_count = db.query(Case).filter(Case.user_id == u.id).count()
            print(f"ID: {u.id}, Username: {u.username}, Case Count: {case_count}")
    
    print("\nALL USERS:")
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}")

    db.close()

if __name__ == "__main__":
    check()
