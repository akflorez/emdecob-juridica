import os
import asyncio
import traceback
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Force emdecob_consultas database
os.environ["DATABASE_URL"] = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

from backend.db import SessionLocal
from backend.models import Case, CasePublicationSearch
from backend.service.publicaciones import consultar_publicaciones_rango, guardar_publicacion_validada

async def main():
    db = SessionLocal()
    search_id = 7109  # ID 7109 (2026-05)
    
    candidato = db.query(CasePublicationSearch).filter(CasePublicationSearch.id == search_id).first()
    if not candidato:
        print(f"Candidate {search_id} not found.")
        db.close()
        return

    print(f"--- Processing Candidate ID={candidato.id} Mes={candidato.mes_busqueda} ---")
    candidato.estado = "procesando"
    candidato.estado_busqueda = "procesando"
    db.commit()
    
    try:
        fecha_act_str = candidato.fecha_actuacion.strftime("%Y-%m-%d")
        year, month = map(int, candidato.mes_busqueda.split("-"))
        
        case_obj = db.query(Case).filter(Case.radicado == candidato.radicado, Case.company_id == candidato.company_id).first()
        demandante = case_obj.demandante if case_obj else ""
        demandado = case_obj.demandado if case_obj else ""
        
        print(f"Running scraper for mes {candidato.mes_busqueda}...")
        pubs = await consultar_publicaciones_rango(
            candidato.radicado, 
            fecha_act_str, 
            demandante=demandante,
            demandado=demandado,
            year=year, 
            month=month,
            company_id=candidato.company_id,
            search_id=candidato.id
        )
        
        print(f"Scraper returned {len(pubs)} publication results.")
        
        has_visible = False
        if pubs:
            for pub_data in pubs:
                pub_data["radicado"] = candidato.radicado
                saved_pub = guardar_publicacion_validada(db, pub_data, search_id=candidato.id)
                if saved_pub:
                    print(f"Saved Publication: ID={saved_pub.id}, EstadoValidacion={saved_pub.estado_validacion}, Score={saved_pub.match_score}")
                    if saved_pub.estado_validacion in ["validado", "validado_automatico", "validado_por_fuente_oficial"]:
                        has_visible = True
                        
        if has_visible:
            candidato.estado = "encontrada"
            candidato.estado_busqueda = "encontrada"
        else:
            candidato.estado = "sin_resultado"
            candidato.estado_busqueda = "sin_resultado"
            
        candidato.processed_at = datetime.now()
        candidato.ultimo_error = None
        db.commit()
        print(f"Candidate processed. Final status in DB: {candidato.estado}")
        
    except Exception as e:
        db.rollback()
        print(f"Error during processing: {e}")
        traceback.print_exc()

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
