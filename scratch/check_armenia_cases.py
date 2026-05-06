
from backend.db import SessionLocal
from backend.models import Case, User
from sqlalchemy import or_

def check():
    db = SessionLocal()
    # Armenia radicados often start with 63001
    search = "63001%"
    cases = db.query(Case).filter(Case.radicado.like(search)).all()
    print(f"Cases starting with 63001: {len(cases)}")
    
    uids = {}
    for c in cases:
        uids[c.user_id] = uids.get(c.user_id, 0) + 1
    
    for uid, count in uids.items():
        u = db.query(User).filter(User.id == uid).first()
        uname = u.username if u else "None"
        print(f"  User ID: {uid} ({uname}), Count: {count}")
    
    db.close()

if __name__ == "__main__":
    check()
