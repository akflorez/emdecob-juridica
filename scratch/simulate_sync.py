import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Case, CaseEvent
from backend.service.rama import actuaciones_proceso
from backend.main import sha256_obj

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(DATABASE_URL)
CustomSession = sessionmaker(bind=engine)

async def simulate():
    db = CustomSession()
    try:
        c = db.query(Case).filter(Case.id == 1470).first()
        if not c:
            print("Case 1470 not found in DB")
            return
            
        print(f"Case: {c.radicado} | id_proceso: {c.id_proceso}")
        
        acts = await actuaciones_proceso(int(c.id_proceso))
        print(f"Acts from API: {len(acts)}")
        
        for a in acts:
            it = {
                "event_date": a.get("fechaActuacion"),
                "title": (a.get("actuacion") or "").strip(),
                "detail": a.get("anotacion"),
            }
            event_hash = sha256_obj(it)
            con_docs = bool(a.get("conDocumentos"))
            
            exists = db.query(CaseEvent).filter(
                CaseEvent.case_id == c.id,
                CaseEvent.event_hash == event_hash
            ).first()
            
            fallback = False
            if not exists:
                exists = db.query(CaseEvent).filter(
                    CaseEvent.case_id == c.id,
                    CaseEvent.event_date == it["event_date"],
                    CaseEvent.title == it["title"],
                    CaseEvent.detail == it["detail"]
                ).first()
                if exists:
                    fallback = True
            
            print(f"\nActuacion: {it['title']} | Date: {it['event_date']}")
            print(f"  conDocumentos from API: {con_docs}")
            if exists:
                print(f"  Found in DB! ID: {exists.id} | Hash in DB: {exists.event_hash} | it Hash: {event_hash} | FallbackMatch: {fallback}")
                print(f"  DB values: id_reg_actuacion: {exists.id_reg_actuacion} | cons_actuacion: {exists.cons_actuacion} | con_docs_db: {exists.con_documentos}")
                
                # Check condition
                cond = con_docs and (not exists.id_reg_actuacion or not exists.cons_actuacion)
                print(f"  Should update condition `con_docs and (not exists.id_reg_actuacion or not exists.cons_actuacion)`: {cond}")
                
                if cond:
                    print("  Updating technical IDs in DB simulation...")
                    exists.id_reg_actuacion = a.get("idRegActuacion")
                    exists.cons_actuacion = a.get("consActuacion")
                    exists.con_documentos = True
                    print(f"  Updated values -> id_reg: {exists.id_reg_actuacion} | cons: {exists.cons_actuacion}")
            else:
                print("  NOT found in DB!")
                
        # Do not commit, just inspect
        print("\nRollback changes.")
        db.rollback()
    finally:
        db.close()

asyncio.run(simulate())
