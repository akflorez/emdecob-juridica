
from backend.db import SessionLocal
from backend.models import Case, User

def check():
    db = SessionLocal()
    uids = db.query(Case.user_id).distinct().all()
    print("Unique user_ids in Case table:")
    for (uid,) in uids:
        u = db.query(User).filter(User.id == uid).first()
        uname = u.username if u else "NON-EXISTENT USER"
        count = db.query(Case).filter(Case.user_id == uid).count()
        print(f"ID: {uid}, Username: {uname}, Count: {count}")
    db.close()

if __name__ == "__main__":
    check()
