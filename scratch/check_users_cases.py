
from backend.db import SessionLocal
from backend.models import User, Case


def check():
    db = SessionLocal()
    users = db.query(User).all()
    print("Users in DB (Filtered):")
    for u in users:
        uname = u.username.lower()
        if "juri" in uname or u.id == 2:
            case_count = db.query(Case).filter(Case.user_id == u.id).count()
            print(f"ID: {u.id}, Username: {u.username}, Case Count: {case_count}")
    
    orphan_cases = db.query(Case).filter(Case.user_id == None).count()
    print(f"Orphan cases (user_id is None): {orphan_cases}")
    
    db.close()


if __name__ == "__main__":
    check()
