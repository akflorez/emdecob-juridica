
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Case, CaseEvent

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
LOCAL_DB = os.getenv("DATABASE_URL")

def transfer_events():
    e_local = create_engine(LOCAL_DB)
    db_local = sessionmaker(bind=e_local)()

    e_prod = create_engine(NEON_URL)
    db_prod = sessionmaker(bind=e_prod)()

    # 1. Mapear radicados de local a sus IDs locales
    # 2. Encontrar los mismos radicados en Neon para saber su New ID
    
    # Por simplicidad y dado que los IDs de radicados podrian no coincidir...
    # Usaremos el radicado como puente.
    
    print("Iniciando transferencia de Actuaciones a Juricob...")
    
    local_cases = db_local.query(Case).all()
    case_map = {c.radicado: c.id for c in local_cases}
    
    neon_cases = db_prod.query(Case).all()
    neon_map = {c.radicado: c.id for c in neon_cases}
    
    count = 0
    for radicado, local_id in case_map.items():
        neon_id = neon_map.get(radicado)
        if not neon_id: continue
        
        # Obtener actuaciones locales
        local_evs = db_local.query(CaseEvent).filter(CaseEvent.case_id == local_id).all()
        for ev in local_evs:
            # Evitar duplicados por hash
            exists = db_prod.query(CaseEvent).filter(CaseEvent.case_id == neon_id, CaseEvent.event_hash == ev.event_hash).first()
            if not exists:
                new_ev = CaseEvent(
                    case_id=neon_id,
                    event_date=ev.event_date,
                    title=ev.title,
                    detail=ev.detail,
                    event_hash=ev.event_hash,
                    con_documentos=ev.con_documentos
                )
                db_prod.add(new_ev)
                count += 1
                if count % 100 == 0:
                    db_prod.commit()
                    print(f"Subidas {count} actuaciones...")

    db_prod.commit()
    print(f"Transferencia finalizada: {count} actuaciones nuevas en Juricob.")
    db_local.close()
    db_prod.close()

if __name__ == "__main__":
    transfer_events()
