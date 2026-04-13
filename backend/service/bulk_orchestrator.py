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

        results = {} # Usamos dict para manejar reintentos fácilmente
        failed_indices = []

        async def process_row(idx, row_data, is_retry=False, date_range=None):
            try:
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
                    prefix = "🔄 [REINTENTO]" if is_retry else "🔍"
                    log_job(f"{prefix} [{idx}] {name1}")
                    try:
                        res1 = await asyncio.wait_for(consulta_por_nombre(name1, id_depto=id_depto), timeout=30.0)
                        if res1 and res1.get("procesos"):
                            found_for_row.extend(res1["procesos"])
                    except asyncio.TimeoutError:
                        log_job(f"⚠️ [{idx}] Timeout Name1 (30s)")
                        return False # Marcar para reintento
                    except Exception as e:
                        log_job(f"⚠️ [{idx}] Error Name1: {e}")
                        return False # Marcar para reintento

                # Si no hay resultados, intentar Nombre 2
                if not found_for_row and name2 and name2.lower() != "nan":
                    log_job(f"🔍 [{idx}] {name2} (Fallback)")
                    try:
                        res2 = await asyncio.wait_for(consulta_por_nombre(name2, id_depto=id_depto), timeout=30.0)
                        if res2 and res2.get("procesos"):
                            found_for_row.extend(res2["procesos"])
                    except asyncio.TimeoutError:
                        log_job(f"⚠️ [{idx}] Timeout Name2 (30s)")
                        return False
                    except Exception as e:
                        log_job(f"⚠️ [{idx}] Error Name2: {e}")
                        return False

                # Seleccionar mejor radicado con filtro de fechas
                best_radicado = None
                if found_for_row:
                    def get_sort_key(p):
                        f_ult = p.get("fechaUltimaActuacion") or p.get("FechaUltimaActuacion") or ""
                        f_rad = p.get("fechaRadicacion") or p.get("FechaRadicacion") or ""
                        return max(f_ult, f_rad)
                    
                    # Filtrar por fecha si el usuario lo pidió
                    if date_range and (date_range.get("from") or date_range.get("to")):
                        df_from = date_range.get("from")
                        df_to = date_range.get("to")
                        
                        filtered = []
                        for p in found_for_row:
                            p_rad_date_raw = p.get("fechaRadicacion") or p.get("FechaRadicacion") or ""
                            p_rad_date = p_rad_date_raw[:10] # Tomar solo YYYY-MM-DD
                            
                            is_ok = True
                            if df_from and p_rad_date and p_rad_date < df_from:
                                is_ok = False
                            if df_to and p_rad_date and p_rad_date > df_to:
                                is_ok = False
                            
                            if is_ok:
                                # Normalizar para que el resto del sistema vea solo la fecha
                                if "fechaRadicacion" in p: p["fechaRadicacion"] = p_rad_date
                                if "FechaRadicacion" in p: p["FechaRadicacion"] = p_rad_date
                                if "fechaUltimaActuacion" in p and p["fechaUltimaActuacion"]:
                                    p["fechaUltimaActuacion"] = p["fechaUltimaActuacion"][:10]
                                filtered.append(p)
                        
                        if filtered:
                            best_radicado = max(filtered, key=get_sort_key)
                        else:
                            best_radicado = None # Ninguno en el rango
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
                return True
            except Exception as e:
                log_job(f"💥 [{idx}] Error inesperado: {e}")
                results[idx] = {"index": idx, "error": str(e)}
                return False

        # --- PRIMERA PASADA ---
        log_job(f"--- PRIMERA PASADA ({total} filas) ---")
        for index, row in df.iterrows():
            success = await process_row(index, row, is_retry=False, date_range=date_range)
            if not success:
                failed_indices.append(index)
            
            job.processed_items = index + 1
            if index % 5 == 0 or index == total - 1:
                log_job(f"📊 Progreso: {index + 1}/{total}")
                db.commit()
            await asyncio.sleep(1.0)

        # --- SEGUNDA PASADA (REINTENTOS) ---
        if failed_indices:
            log_job(f"--- SEGUNDA PASADA (REINTENTOS) para {len(failed_indices)} filas ---")
            for i, idx in enumerate(failed_indices):
                row = df.iloc[idx]
                await process_row(idx, row, is_retry=True, date_range=date_range)
                log_job(f"🔄 Reintento {i+1}/{len(failed_indices)} ok")
                db.commit()
                await asyncio.sleep(3.0)

        # Convertir a lista final ordenada
        final_results = [results[i] for i in sorted(results.keys())]
        
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
