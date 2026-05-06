
from backend.db import SessionLocal
from backend.models import Case

def check():
    db = SessionLocal()
    count = db.query(Case).filter(Case.user_id == 1, Case.abogado == "santiago quintero").count()
    print(f"Cases with abogado 'santiago quintero' owned by ID 1 (FNA): {count}")
    
    count2 = db.query(Case).filter(Case.user_id == 2, Case.abogado == "santiago quintero").count()
    print(f"Cases with abogado 'santiago quintero' owned by ID 2 (Jurico): {count2}")
    
    db.close()

if __name__ == "__main__":
    check()
