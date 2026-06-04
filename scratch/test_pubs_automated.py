import os
import sys
import asyncio

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db import SessionLocal
from backend.models import Case, CaseEvent
from backend.main import save_new_publications

async def run_test():
    db = SessionLocal()
    try:
        # Find or create Case 63001311000320250043600
        radicado = "63001311000320250043600"
        case = db.query(Case).filter(Case.radicado == radicado).first()
        
        if not case:
            print(f"[test] Creating temporary case for {radicado}")
            case = Case(
                radicado=radicado,
                demandante="FONDO NACIONAL DE AHORRO",
                demandado="AUGUSTO PAVANI",
                user_id=1
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            
        # Ensure there is a relevant event on April 17, 2026
        event_date = "2026-04-17"
        event = db.query(CaseEvent).filter(
            CaseEvent.case_id == case.id,
            CaseEvent.event_date == event_date
        ).first()
        
        if not event:
            print(f"[test] Creating relevant event on {event_date}")
            event = CaseEvent(
                case_id=case.id,
                event_date=event_date,
                title="FIJACION DE ESTADO NO. 041",
                detail="Notificación por estado",
                event_hash="test_hash_12345"
            )
            db.add(event)
            db.commit()
            
        print(f"[test] Running sync for case {case.radicado} (ID: {case.id})...")
        await save_new_publications(case, db, force=True)
        
        # Query case publications to inspect them
        from backend.models import CasePublication
        pubs = db.query(CasePublication).filter(CasePublication.case_id == case.id).all()
        print(f"\n[test] Sync completed. Found {len(pubs)} saved publications.")
        
        for i, pub in enumerate(pubs):
            print(f"\n=== Publication #{i+1} ===")
            print(f"  ID: {pub.id}")
            print(f"  Fecha Publicación: {pub.fecha_publicacion}")
            print(f"  Descripción: {pub.descripcion}")
            print(f"  Doc Principal: {pub.url_fuente_principal}")
            print(f"  Tipo Principal: {pub.tipo_fuente_principal}")
            print(f"  Providencia URL: {pub.url_providencia}")
            print(f"  Doc. Complementarios:")
            
            if pub.documentos_complementarios:
                import json
                docs = json.loads(pub.documentos_complementarios)
                for d in docs:
                    print(f"    - Name: {d.get('nombre')}")
                    print(f"      URL: {d.get('url')}")
                    print(f"      Contains Radicado: {d.get('contiene_radicado')}")
                    print(f"      Match Type: {d.get('match_type')}")
                    print(f"      Observation: {d.get('observacion')}")
            else:
                print("    (None)")
                
    except Exception as e:
        print(f"[test] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_test())
