
from backend.db import SessionLocal
from backend.models import Case, User

def check():
    db = SessionLocal()
    # Check for cases that might belong to Emdecob but are assigned to FNA
    cases = db.query(Case).filter(Case.user_id == 1).all()
    count = 0
    for c in cases:
        belongs_to_emdecob = False
        if c.abogado and ("SANTIAGO" in c.abogado.upper() or "EMDECOB" in c.abogado.upper()):
            belongs_to_emdecob = True
        if c.demandante and "EMDECOB" in c.demandante.upper():
            belongs_to_emdecob = True
        if c.demandado and "EMDECOB" in c.demandado.upper():
            belongs_to_emdecob = True
        
        if belongs_to_emdecob:
            count += 1
            if count <= 10:
                print(f"Potential Emdecob case in FNA: ID={c.id}, Radicado={c.radicado}, Abogado={c.abogado}")
    
    print(f"Total potential Emdecob cases in FNA: {count}")
    db.close()

if __name__ == "__main__":
    check()
