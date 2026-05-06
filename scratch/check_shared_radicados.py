
from backend.db import SessionLocal
from backend.models import Case
from sqlalchemy import func

def check():
    db = SessionLocal()
    dupes = db.query(Case.radicado).group_by(Case.radicado).having(func.count(Case.id) > 1).all()
    print(f"Total radicados with duplicates: {len(dupes)}")
    
    for (rad,) in dupes:
        users = db.query(Case.user_id).filter(Case.radicado == rad).all()
        user_ids = [u[0] for u in users]
        if 1 in user_ids and 2 in user_ids:
            print(f"SHARED Radicado: {rad} (Users: {user_ids})")
    
    db.close()

if __name__ == "__main__":
    check()
