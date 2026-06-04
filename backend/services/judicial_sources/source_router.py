import time
from datetime import datetime
import json
from sqlalchemy.orm import Session
from . import CONNECTORS
from .config import JUDICIAL_SOURCE_URLS
from backend.models import CaseSourceCheck

async def run_multisource_check(
    radicado: str, 
    company_id: int, 
    case_id: int = None, 
    sources: list = None, 
    dry_run: bool = True, 
    db: Session = None
) -> list:
    """
    Orchestrates calling specified sources for a given radicado.
    Calculates search duration, returns formatted statuses, and logs results 
    to case_source_checks DB table when dry_run is False.
    """
    if not sources:
        sources = list(CONNECTORS.keys())
        
    results = []
    
    for src in sources:
        connector = CONNECTORS.get(src)
        if not connector:
            results.append({
                "source": src,
                "status": "unsupported",
                "url": "",
                "records_found": 0,
                "message": f"Fuente '{src}' no configurada en este servidor.",
                "duration_ms": 0
            })
            continue
            
        start_time = time.time()
        status = "pending"
        url = connector.config.get("base_url", connector.config.get("consulta_url", ""))
        records_found = 0
        error_message = None
        raw_summary = {}
        
        try:
            # Check supports
            if not connector.supports(radicado):
                status = "unsupported"
                message = "Formato de radicado no soportado por esta fuente."
            else:
                # Execute search stub (Fase 1 dry run stubbing)
                res = connector.search_case(radicado)
                status = res.get("status", "success")
                message = res.get("message", "Consulta completada en modo diagnóstico.")
                url = res.get("url", url)
                
                # Fetch mock events count
                if status == "success":
                    events = connector.search_events(radicado)
                    records_found = len(events)
                    raw_summary = {
                        "events_count": records_found,
                        "data": res.get("data", {})
                    }
                else:
                    message = res.get("message", "Fuente requiere captcha o interacción manual.")
        except Exception as e:
            status = "error"
            error_message = str(e)
            message = f"Error en la consulta: {error_message}"
            
        duration_ms = int((time.time() - start_time) * 1000)
        
        results.append({
            "source": src,
            "status": status,
            "url": url,
            "records_found": records_found,
            "message": message,
            "duration_ms": duration_ms
        })
        
        # Persist status in DB when db is provided (case_source_checks is the log of the check)
        if db is not None:
            try:
                db_log = CaseSourceCheck(
                    company_id=company_id,
                    case_id=case_id,
                    radicado=radicado,
                    source=src,
                    source_url=url,
                    status=status,
                    checked_at=datetime.utcnow(),
                    duration_ms=duration_ms,
                    error_message=error_message,
                    records_found=records_found,
                    raw_summary=json.dumps(raw_summary) if raw_summary else None,
                    created_at=datetime.utcnow()
                )
                db.add(db_log)
                db.commit()
            except Exception as db_err:
                print(f"[DB-ERROR] Error logging source check for {src}: {db_err}")
                db.rollback()
                
    return results
