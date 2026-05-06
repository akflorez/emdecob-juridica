
from backend.db import SessionLocal
from backend.models import Case

def check():
    db = SessionLocal()
    cases = db.query(Case).filter(Case.user_id == 2).limit(5).all()
    print("Sample cases for User ID 2:")
    for c in cases:
        print(f"ID: {c.id}, Radicado: {c.radicado}, Abogado: {c.abogado}, Demandante: {c.demandante}")
    db.close()

if __name__ == "__main__":
    check()
