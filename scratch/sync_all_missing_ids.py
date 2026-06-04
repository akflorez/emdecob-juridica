import os
import sys
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from backend.models import Case, CaseEvent
from backend.service.rama import actuaciones_proceso
from backend.main import sha256_obj

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(DATABASE_URL)
CustomSession = sessionmaker(bind=engine)

async def sync_case(db, c):
    if not c.id_proceso:
        print(f"Skipping Case ID={c.id} (radicado={c.radicado}): No id_proceso found.")
        return False
        
    print(f"Syncing Case ID={c.id} (radicado={c.radicado}, id_proceso={c.id_proceso})...")
    try:
        acts = await actuaciones_proceso(int(c.id_proceso))
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
                    
        print(f"  -> Updated {updated_count} events with technical IDs.")
        db.commit()
        return True
    except Exception as e:
        print(f"  -> Error syncing case {c.id}: {e}")
        db.rollback()
        return False

async def main():
    db = CustomSession()
    try:
        # Find all cases with events marked con_documentos=True but id_reg_actuacion IS NULL
        cases_to_sync = db.query(Case).join(CaseEvent).filter(
            CaseEvent.con_documentos == True,
            CaseEvent.id_reg_actuacion == None
        ).distinct().all()
        
        print(f"Found {len(cases_to_sync)} cases to sync.")
        
        for idx, c in enumerate(cases_to_sync):
            print(f"Progress: {idx+1}/{len(cases_to_sync)}")
            success = await sync_case(db, c)
            if success:
                # Sleep to avoid overloading the API
                await asyncio.sleep(1.0)
            else:
                await asyncio.sleep(0.5)
                
        print("\nAll cases synced successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
