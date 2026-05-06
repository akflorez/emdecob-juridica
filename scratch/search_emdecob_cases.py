
from backend.db import SessionLocal
from backend.models import Case, User
from sqlalchemy import or_

def check():
    db = SessionLocal()
    search = "%emdecob%"
    cases = db.query(Case).filter(or_(
        Case.radicado.like(search),
        Case.demandante.like(search),
        Case.demandado.like(search),
        Case.abogado.like(search),
        Case.alias.like(search)
    )).all()
    
    print(f"Cases matching 'emdecob': {len(cases)}")
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
