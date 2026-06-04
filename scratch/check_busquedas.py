import os
import sys

sys.path.append(os.getcwd())
from backend.db import SessionLocal
from backend.models import CasePublicationSearch

def main():
    db = SessionLocal()
    try:
        rad = "11001400300720250052200"
        records = db.query(CasePublicationSearch).filter(CasePublicationSearch.radicado == rad).all()
        print(f"Total search records in DB: {len(records)}")
        
        for idx, r in enumerate(records):
            print(f"[{idx+1:02d}] Rango={r.fecha_inicio_busqueda} a {r.fecha_fin_busqueda} | Estado={r.estado} | Ultima Busqueda={r.fecha_ultima_busqueda} | Error={r.error}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
