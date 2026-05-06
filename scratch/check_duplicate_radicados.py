
from backend.db import SessionLocal
from backend.models import Case
from sqlalchemy import func

def check():
    db = SessionLocal()
    # Find duplicate radicados
    dupes = db.query(Case.radicado, func.count(Case.id)).group_by(Case.radicado).having(func.count(Case.id) > 1).all()
    print(f"Duplicate radicados found: {len(dupes)}")
    for rad, count in dupes[:10]:
        print(f"  Radicado: {rad}, Count: {count}")
        cases = db.query(Case).filter(Case.radicado == rad).all()
        for c in cases:
            print(f"    - ID: {c.id}, User ID: {c.user_id}, ID Proceso: {c.id_proceso}, Juzgado: {c.juzgado}")
    
    db.close()

if __name__ == "__main__":
    check()
