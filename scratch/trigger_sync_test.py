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

async def run_test_sync():
    db = CustomSession()
    try:
        c = db.query(Case).filter(Case.id == 1470).first()
        if not c:
            print("Case 1470 not found")
            return
            
        print(f"Case before sync: radicado={c.radicado} | id_proceso={c.id_proceso} | last_check_at={c.last_check_at}")
        
        # Count events without id_reg_actuacion
        no_id_count = db.query(CaseEvent).filter(CaseEvent.case_id == c.id, CaseEvent.con_documentos == True, CaseEvent.id_reg_actuacion == None).count()
        print(f"Events with con_documentos=True but id_reg_actuacion=None: {no_id_count}")
        
        # Sincronizar
        from backend.main import sync_case_events_background
        # Espera, sync_case_events_background uses SessionLocal from backend.db, so it would run on 'juricob' database!
        # Since we want to run it on 'emdecob_consultas', we can just run the loop logic here but committing to 'emdecob_consultas'!
        
        print("\nRunning sync loop on emdecob_consultas...")
        acts = await actuaciones_proceso(int(c.id_proceso))
        print(f"Total acts from API: {len(acts)}")
        
        updated_count = 0
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
            
            if not exists:
                exists = db.query(CaseEvent).filter(
                    CaseEvent.case_id == c.id,
                    CaseEvent.event_date == it["event_date"],
                    CaseEvent.title == it["title"],
                    CaseEvent.detail == it["detail"]
                ).first()
                if exists:
                    exists.event_hash = event_hash
                    
            if exists:
                if con_docs and (not exists.id_reg_actuacion or not exists.cons_actuacion):
                    exists.id_reg_actuacion = a.get("idRegActuacion")
                    exists.cons_actuacion = a.get("consActuacion")
                    exists.con_documentos = True
                    c.has_documents = True
                    updated_count += 1
                    
        print(f"Updated {updated_count} events with technical IDs.")
        db.commit()
        
        # Verify
        no_id_count_after = db.query(CaseEvent).filter(CaseEvent.case_id == c.id, CaseEvent.con_documentos == True, CaseEvent.id_reg_actuacion == None).count()
        print(f"Events with con_documentos=True but id_reg_actuacion=None AFTER sync: {no_id_count_after}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

asyncio.run(run_test_sync())
