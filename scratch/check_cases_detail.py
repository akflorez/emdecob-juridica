
from backend.db import SessionLocal
from backend.models import User, Case

def check():
    db = SessionLocal()
    u2 = db.query(User).filter(User.id == 2).first()
    if u2:
        valid_cases = db.query(Case).filter(Case.user_id == 2, Case.juzgado.isnot(None)).count()
        pending_cases = db.query(Case).filter(Case.user_id == 2, Case.juzgado.is_(None)).count()
        print(f"User ID 2 ({u2.username}):")
        print(f"  Valid cases: {valid_cases}")
        print(f"  Pending cases: {pending_cases}")
    else:
        print("User ID 2 not found")
    db.close()

if __name__ == "__main__":
    check()
