import sys
import os
sys.path.append(os.getcwd())
from backend.db import SessionLocal
from backend.models import Case, CasePublication
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        rad = "11001400302420240140300"
        case = db.query(Case).filter(Case.radicado == rad).first()
        if not case:
            print(f"Case with radicado {rad} not found!")
            return
        
        print(f"Case found: ID={case.id}, Radicado={case.radicado}")
        print(f"Demandante: {case.demandante}")
        print(f"Demandado: {case.demandado}")
        print(f"Sync Status: {case.sync_pub_status}")
        print(f"Sync Progress: {case.sync_pub_progress}")
        
        # 1. Print current publications for this case
        pubs = db.query(CasePublication).filter(CasePublication.case_id == case.id).all()
        print(f"\nPublications in DB (Total {len(pubs)}):")
        for i, p in enumerate(pubs):
            print(f"  #{i+1}: ID={p.id}, Fecha={p.fecha_publicacion}, Tipo={p.tipo_publicacion}, Desc={p.descripcion[:100]}, URL={p.documento_url}")
            
        # 2. Print sync debug logs
        print("\nLast 15 Sync Debug Logs:")
        logs = db.execute(text("SELECT id, message, created_at FROM sync_debug_logs WHERE case_id = :cid ORDER BY created_at DESC LIMIT 15"), 
                          {"cid": case.id}).fetchall()
        for l in logs:
            print(f"  [{l[2]}] {l[1]}")
            
    finally:
        db.close()

if __name__ == '__main__':
    main()
