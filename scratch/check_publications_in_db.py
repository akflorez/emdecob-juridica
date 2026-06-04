import os
import sys

sys.path.append(os.getcwd())
from backend.db import SessionLocal
from backend.models import Case, CasePublication

def main():
    db = SessionLocal()
    try:
        rad = "11001400300720250052200"
        case = db.query(Case).filter(Case.radicado == rad).first()
        if not case:
            print(f"Case with radicado {rad} not found!")
            return
            
        pubs = db.query(CasePublication).filter(CasePublication.case_id == case.id).all()
        print(f"Total publications saved in DB: {len(pubs)}")
        
        for idx, pub in enumerate(pubs):
            print(f"[{idx+1:02d}] Fecha Pub={pub.fecha_publicacion} | Estado No={pub.numero_estado} | Tipo={pub.tipo_publicacion} | Desc={pub.descripcion[:60]}...")
            print(f"     Doc URL={pub.url_fuente_principal}")
            print(f"     Match Type={pub.match_type} | Match Fuerte={pub.match_fuerte}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
