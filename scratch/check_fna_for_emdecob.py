
from backend.db import SessionLocal
from backend.models import Case, User

def check():
    db = SessionLocal()
    cases = db.query(Case).filter(Case.user_id == 1).limit(100).all()
    print("Sample cases for User ID 1 (FNA):")
    for c in cases:
        if c.demandante and ("EMDECOB" in c.demandante.upper() or "SANTIAGO" in c.demandante.upper()):
            print(f"ID: {c.id}, Radicado: {c.radicado}, Demandante: {c.demandante}")
        if c.demandado and ("EMDECOB" in c.demandado.upper() or "SANTIAGO" in c.demandado.upper()):
            print(f"ID: {c.id}, Radicado: {c.radicado}, Demandado: {c.demandado}")
    
    db.close()

if __name__ == "__main__":
    check()
