import asyncio
import pandas as pd
import json
from io import BytesIO
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

from .rama import consulta_por_nombre, RamaError
from ..models import SearchJob, Case, CaseEvent

def log_job(msg):
    with open("search_job.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

# Mapping aproximado de departamentos a IDs de Rama Judicial (2 dígitos)
DEPARTAMENTO_MAP = {
    "ANTIOQUIA": "05",
    "ATLANTICO": "08",
    "BOGOTA": "11",
    "BOLIVAR": "13",
    "BOYACA": "15",
    "CALDAS": "17",
    "CAQUETA": "18",
    "CAUCA": "19",
    "CESAR": "20",
    "CORDOBA": "23",
    "CUNDINAMARCA": "25",
    "CHOCO": "27",
    "HUILA": "41",
    "LA GUAJIRA": "44",
    "MAGDALENA": "47",
    "META": "50",
    "NARINO": "52",
    "NORTE DE SANTANDER": "54",
    "QUINDIO": "63",
    "RISARALDA": "66",
    "SANTANDER": "68",
    "SUCRE": "70",
    "TOLIMA": "73",
    "VALLE DEL CAUCA": "76",
    "ARAUCA": "81",
    "CASANARE": "85",
    "PUTUMAYO": "86",
    "SAN ANDRES": "88",
    "AMAZONAS": "91",
    "GUAINIA": "94",
    "GUAVIARE": "95",
    "VAUPES": "97",
    "VICHADA": "99",
}

async def run_name_search_job(job_id: int, file_content: bytes, db_factory, date_range: dict | None = None):
    """
    Orquestador de búsqueda por nombres en segundo plano.
    """
    db = db_factory()
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        db.close()
        return

    try:
        log_job(f"🚀 Iniciando trabajo {job_id}")
        if date_range:
            log_job(f"📅 Filtro de fechas: {date_range.get('from')} - {date_range.get('to')}")
        job.status = "processing"
        db.commit()

        # 1. Parsear Excel
        log_job(f"Reading excel content...")
        df = pd.read_excel(BytesIO(file_content))
        # Columnas esperadas: Departamento, Demandado 1, Demandado 2, Cedula, Abogado
        # Normalizamos nombres de columnas (insensible a mayúsculas/tildes)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        total = len(df)
        job.total_items = total
        db.commit()

        results = {}
        failed_indices = []

        async def process_row(idx, row_data, is_retry=False, date_range=None):
            try:
                # Inicializar entrada para evitar KeyError
                if idx not in results:
                    results[idx] = {"index": idx, "input_name1": "", "found_count": 0, "selected": None}
                
                # Extraer datos con fallbacks
                depto_name = str(row_data.get("DEPARTAMENTO", "")).strip().upper()
                name1 = str(row_data.get("DEMANDADO 1", row_data.get("NOMBRE 1", ""))).strip()
                name2 = str(row_data.get("DEMANDADO 2", row_data.get("NOMBRE 2", ""))).strip()
                cedula = str(row_data.get("CEDULA", "")).strip()
                abogado = str(row_data.get("ABOGADO", "")).strip()

                id_depto = DEPARTAMENTO_MAP.get(depto_name, "00")
                found_for_row = []

                # Búsqueda secuencial: Intentar Nombre 1
                if name1 and name1.lower() != "nan":
                    try:
                        res1 = await asyncio.wait_for(consulta_por_nombre(name1, id_depto=id_depto), timeout=45.0)
                        if res1 and res1.get("procesos"):
                            found_for_row.extend(res1["procesos"])
                    except Exception as e:
                        log_job(f"⚠️ [{idx}] Error Name1: {e}")
                        # No retornamos False aquí para permitir que intente Name2

                # Si no hay resultados, intentar Nombre 2
                if not found_for_row and name2 and name2.lower() != "nan":
                    try:
                        res2 = await asyncio.wait_for(consulta_por_nombre(name2, id_depto=id_depto), timeout=45.0)
                        if res2 and res2.get("procesos"):
                            found_for_row.extend(res2["procesos"])
                    except Exception as e:
                        log_job(f"⚠️ [{idx}] Error Name2: {e}")

                # Seleccionar mejor radicado con filtro de fechas
                best_radicado = None
                if found_for_row:
                    def get_sort_key(p):
                        f_ult = p.get("fechaUltimaActuacion") or p.get("FechaUltimaActuacion") or ""
                        f_rad = p.get("fechaRadicacion") or p.get("FechaRadicacion") or ""
                        return max(f_ult, f_rad)
                    
                    if date_range and (date_range.get("from") or date_range.get("to")):
                        df_from = date_range.get("from")
                        df_to = date_range.get("to")
                        filtered = []
                        for p in found_for_row:
                            p_rad_date_raw = p.get("fechaRadicacion") or p.get("FechaRadicacion") or ""
                            p_rad_date = p_rad_date_raw[:10]
                            is_ok = True
                            if df_from and p_rad_date and p_rad_date < df_from: is_ok = False
                            if df_to and p_rad_date and p_rad_date > df_to: is_ok = False
                            if is_ok:
                                if "fechaRadicacion" in p: p["fechaRadicacion"] = p_rad_date
                                if "FechaRadicacion" in p: p["FechaRadicacion"] = p_rad_date
                                filtered.append(p)
                        if filtered:
                            best_radicado = max(filtered, key=get_sort_key)
                    else:
                        best_radicado = max(found_for_row, key=get_sort_key)

                results[idx] = {
                    "index": idx,
                    "input_name1": name1,
                    "input_name2": name2,
                    "cedula": cedula,
                    "abogado": abogado,
                    "found_count": len(found_for_row),
                    "selected": best_radicado,
                    "all_options": found_for_row[:5]
                }
                return True if found_for_row else False
            except Exception as e:
                log_job(f"💥 [{idx}] Error inesperado: {e}")
                results[idx] = {"index": idx, "input_name1": name1, "error": str(e), "found_count": 0, "selected": None}
                return False

        # --- PROCESAMIENTO POR LOTES (MAX 3 CONCURRENTES PARA NO BLOQUEAR IP) ---
        log_job(f"--- INICIANDO BÚSQUEDA ({total} filas) ---")
        batch_size = 3
        for i in range(0, total, batch_size):
            batch = df.iloc[i : i + batch_size]
            tasks = []
            for index, row in batch.iterrows():
                tasks.append(process_row(index, row, date_range=date_range))
            
            await asyncio.gather(*tasks)
            
            # Actualizar progreso
            processed_so_far = min(i + batch_size, total)
            job.processed_items = processed_so_far
            db.commit()
            
            log_job(f"📊 Progreso: {processed_so_far}/{total}")
            await asyncio.sleep(1.5) # Pausa cortés entre batches

        # Convertir a lista final ordenada (Aseguramos que no falte ningún índice)
        final_results = []
        for i in range(total):
            if i in results:
                final_results.append(results[i])
            else:
                # Fallback por si acaso falló algún batch entero
                final_results.append({"index": i, "input_name1": "Error", "found_count":0, "selected":None})
        
        log_job(f"🏁 Trabajo {job_id} completado")
        job.status = "completed"
        job.results_json = json.dumps(final_results)
        db.commit()

    except Exception as e:
        log_job(f"🔥 ERROR CRÍTICO {job_id}: {e}")
        log_job(traceback.format_exc())
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
