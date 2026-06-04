import os
import asyncio
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Query,
    BackgroundTasks,
    Body,
    Security,
    Request,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, sessionmaker, joinedload, selectinload
from sqlalchemy import create_engine, or_, desc, and_, case as sql_case, func

# IMPORTACION ADAPTATIVA (Expert Mode)
try:
    from backend.db import engine, SessionLocal, Base
except ImportError:
    try:
        from .db import engine, SessionLocal, Base
    except ImportError:
        import db
        engine = db.engine
        SessionLocal = db.SessionLocal
        Base = db.Base

# MIGRACIONES AUTOMATICAS RAPIDAS
from sqlalchemy import text

def try_execute(conn, sql):
    try:
        conn.execute(text(sql))
    except Exception as e:
        print(f"Migración fallida ({sql}): {e}")

try:
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # Migraciones SaaS
        try_execute(conn, """
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                nit VARCHAR(50),
                estado VARCHAR(50) DEFAULT 'activo',
                limite_usuarios INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        try_execute(conn, """
            INSERT INTO companies (id, nombre) 
            SELECT 1, 'Empresa Default' 
            WHERE NOT EXISTS (SELECT 1 FROM companies WHERE id = 1)
        """)

        # Tareas
        try_execute(conn, "ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS user_name VARCHAR(255)")
        try_execute(conn, "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100)")
        try_execute(conn, "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_name VARCHAR(200)")
        try_execute(conn, "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS custom_fields TEXT")
        
        # General
        try_execute(conn, "ALTER TABLE users ADD COLUMN IF NOT EXISTS company_id INTEGER")
        try_execute(conn, "ALTER TABLE cases ADD COLUMN IF NOT EXISTS company_id INTEGER")
        try_execute(conn, "ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS company_id INTEGER")
        
        # Opcional, si audit_logs no existe, fallará silenciosamente sin afectar al resto
        try_execute(conn, "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS company_id INTEGER")
        
        # Migraciones para Documentos Judiciales
        try_execute(conn, "ALTER TABLE case_events ADD COLUMN IF NOT EXISTS id_reg_actuacion BIGINT")
        try_execute(conn, "ALTER TABLE case_events ADD COLUMN IF NOT EXISTS cons_actuacion BIGINT")
        try_execute(conn, "ALTER TABLE case_events ADD COLUMN IF NOT EXISTS documentos_cache TEXT")
        try_execute(conn, "ALTER TABLE cases ADD COLUMN IF NOT EXISTS sync_pub_status VARCHAR(100)")
        try_execute(conn, "ALTER TABLE cases ADD COLUMN IF NOT EXISTS sync_pub_progress INTEGER DEFAULT 0")
        
        # Migraciones para Publicaciones
        try_execute(conn, "ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS mes_busqueda VARCHAR(20)")
        try_execute(conn, "ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS prioridad INTEGER DEFAULT 0")
        
        # TABLA DE LOGS PARA DEBUG
        try_execute(conn, """
            CREATE TABLE IF NOT EXISTS sync_debug_logs (
                id SERIAL PRIMARY KEY,
                case_id INTEGER,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # INDICE PARA VELOCIDAD
        try_execute(conn, "CREATE INDEX IF NOT EXISTS idx_case_pub_case_id ON case_publications(case_id)")
        try_execute(conn, "CREATE INDEX IF NOT EXISTS idx_case_event_case_id ON case_events(case_id)")
        
        print("[DB] Migraciones rapidas completadas")
except Exception as e:
    print(f"[DB] Error en migraciones: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_data_scope(current_user):
    if current_user.username == 'superadmin':
        return {"scope": "all"}
    if current_user.company_id:
        return {"scope": "company", "company_id": current_user.company_id}
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")

def apply_company_filter(query, model, current_user):
    if current_user.username == 'superadmin':
        return query
    if hasattr(model, "company_id"):
        return query.filter(model.company_id == current_user.company_id)
    from fastapi import HTTPException
    raise HTTPException(status_code=500, detail=f"El modelo {model.__name__} requiere filtro por empresa pero no tiene company_id")
from pydantic import BaseModel
from io import BytesIO
import pandas as pd
import traceback
import hashlib
import json
import re
import smtplib
import asyncio
import random
import pytz
import httpx
import os
from passlib.context import CryptContext
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from contextlib import asynccontextmanager

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    nombre: Optional[str] = None
    is_active: bool
    is_admin: bool

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    nombre: Optional[str] = None

class RegisterCompanyRequest(BaseModel):
    company_name: str
    company_nit: Optional[str] = None
    admin_name: str
    email: str
    password: str
    confirm_password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class BillingTierCreate(BaseModel):
    min_cases: int
    max_cases: Optional[int]
    price: float

class BillingTierUpdateList(BaseModel):
    tiers: List[BillingTierCreate]

class LoginRequest(BaseModel):
    username: str
    password: str

from backend.models import (
    Case, CaseEvent, NotificationConfig, NotificationLog, InvalidRadicado, 
    User, CasePublication, SearchJob, Workspace, WorkspaceMember, Folder, 
    ProjectList, Task, TaskComment, TaskChecklistItem, TaskAttachment, IntegrationConfig, Tag,
    Company, Role, PasswordResetToken, BillingTier
)
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.responses import RedirectResponse
from backend.service.rama import (
    consulta_por_radicado,
    detalle_proceso,
    actuaciones_proceso,
    documentos_actuacion,
    consulta_por_nombre,
    RamaError,
    RamaRateLimitError,
)
from backend.apply_robust_migrations import run_migrations
from backend.service.publicaciones import (
    consultar_publicaciones, 
    parse_fecha_pub, 
    consultar_publicaciones_rango,
    is_relevant_actuacion
)
from backend.service.bulk_orchestrator import run_name_search_job, log_job
from backend.clickup_sync import migrate_clickup_to_emdecob


# =========================
# ZONA HORARIA COLOMBIA
# =========================
TIMEZONE_CO = pytz.timezone("America/Bogota")

# Global Lock to prevent multiple background syncs at once
REFRESH_LOCK = asyncio.Lock()

RAMA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://consultaprocesos.ramajudicial.gov.co/",
    "Origin": "https://consultaprocesos.ramajudicial.gov.co",
}

RAMA_BASE = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"

MONTHS_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def now_colombia() -> datetime:
    return datetime.now(TIMEZONE_CO).replace(tzinfo=None)


def today_colombia() -> date:
    return datetime.now(TIMEZONE_CO).date()


# =========================
# VARIABLES GLOBALES AUTO-REFRESH
# =========================
auto_refresh_task = None
auto_refresh_running = False
auto_refresh_stats = {
    "running": False,
    "last_run": None,
    "next_run": None,
    "last_result": None,
    "interval_minutes": 60,
}

_notification_accumulator: List[dict] = []
_notification_accumulator_date: Optional[date] = None
NOTIFICATION_BATCH_SIZE = 15
NOTIFICATION_FLUSH_HOUR = 17


async def notification_flush_loop():
    global _notification_accumulator
    _already_flushed_today: Optional[date] = None

    while True:
        await asyncio.sleep(60)
        try:
            now  = now_colombia()
            hoy  = today_colombia()

            if (
                now.hour == NOTIFICATION_FLUSH_HOUR
                and _already_flushed_today != hoy
                and _notification_accumulator
            ):
                print(f"[flush-loop] Son las {NOTIFICATION_FLUSH_HOUR}:00  enviando {len(_notification_accumulator)} casos acumulados")
                send_grouped_notification(list(_notification_accumulator))
                _notification_accumulator.clear()
                _already_flushed_today = hoy
        except Exception as e:
            with open("sync_emergency.log", "a") as f:
                f.write(f"[{datetime.now()}] ERROR FATAL en tarea {radicado}: {str(e)}\n")
            print(f"[sync-error] {e}")


# =========================
# AUTO-REFRESH EN BACKGROUND
# =========================
async def auto_refresh_loop():
    global auto_refresh_running, auto_refresh_stats

    print("Esperando 60 segundos antes del primer auto-refresh...")
    await asyncio.sleep(60)

    print("Auto-refresh continuo iniciado - revisara TODOS los casos en cada ciclo")

    while auto_refresh_running:
        try:
            now = now_colombia()
            print(f"\n[AUTO-REFRESH] [{now.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando ciclo completo de auto-refresh...")
            auto_refresh_stats["last_run"] = now.isoformat()
            auto_refresh_stats["next_run"] = "Al terminar este ciclo + 10 min"

            result = await do_auto_refresh()

            auto_refresh_stats["last_result"] = result
            print(f"[*] Ciclo completo: {result.get('checked', 0)} revisados, {result.get('updated_cases', 0)} con cambios")

            hora = now_colombia().hour
            if hora >= NOTIFICATION_FLUSH_HOUR and _notification_accumulator:
                print(f"[EMAIL] Flush de 5 PM: enviando {len(_notification_accumulator)} casos acumulados")
                send_grouped_notification(_notification_accumulator)
                _notification_accumulator.clear()

            auto_refresh_stats["next_run"] = "En 10 minutos"
            await asyncio.sleep(600)

        except Exception as e:
            print(f"[ERROR] Error en auto-refresh: {e}")
            auto_refresh_stats["last_result"] = {"error": str(e)}
            await asyncio.sleep(300)


async def do_auto_refresh() -> dict:
    from sqlalchemy import text

    BATCH_SIZE = 3
    MINI_BATCH = 10
    DELAY_BETWEEN = 0.5
    EXTRA_EVERY_N = 10
    EXTRA_DELAY   = 0.5

    updated_cases = []
    checked  = 0
    errors   = 0
    db       = None

    def get_fresh_db():
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
        except Exception:
            session.close()
            session = SessionLocal()
            session.execute(text("SELECT 1"))
        return session

    try:
        db = get_fresh_db()

        BATCH_SIZE = 50

        case_ids = [
            row[0] for row in
            db.query(Case.id)
            .filter(Case.juzgado.isnot(None))
            .order_by(Case.last_check_at.asc())
            .limit(BATCH_SIZE)
            .all()
        ]
        total_cases = db.query(Case).filter(Case.juzgado.isnot(None)).count()
        db.close()
        db = None

        if not case_ids:
            return {"ok": True, "checked": 0, "updated_cases": 0, "message": "No hay casos para verificar"}

        print(f"[stats] Verificando {len(case_ids)} de {total_cases} casos...")

        for i, case_id in enumerate(case_ids):
            try:
                if i > 0:
                    delay = DELAY_BETWEEN + random.uniform(0, 1.0)
                    if i % EXTRA_EVERY_N == 0:
                        delay += EXTRA_DELAY
                    await asyncio.sleep(delay)

                if i % MINI_BATCH == 0:
                    if db:
                        try: db.close()
                        except: pass
                    db = get_fresh_db()
                    print(f"   (Link) Conexion renovada en caso {i+1}/{len(case_ids)}")

                c = db.query(Case).filter(Case.id == case_id).first()
                if not c:
                    continue

                try:
                    resp = await consulta_por_radicado(c.radicado, solo_activos=False, pagina=1)
                    items = extract_items(resp)
                except RamaError as e:
                    print(f"   [WARN] Error consultando {c.radicado}: {e}")
                    errors += 1
                    if "bloque" in str(e).lower() or "rate" in str(e).lower():
                        await asyncio.sleep(60)
                    continue

                if not items:
                    c.last_check_at = now_colombia()
                    checked += 1
                    continue

                p = items[0] or {}

                fecha_ult_api = (
                    p.get("fechaUltimaActuacion")
                    or p.get("FechaUltimaActuacion")
                    or p.get("ultimaActuacion")
                    or p.get("UltimaActuacion")
                )

                nueva_fecha  = parse_fecha(fecha_ult_api)
                fecha_actual = c.ultima_actuacion
                hoy  = today_colombia()
                ayer = hoy - timedelta(days=1)

                hay_cambio           = False
                es_actuacion_reciente = False

                if nueva_fecha and fecha_actual:
                    hay_cambio = nueva_fecha > fecha_actual
                elif nueva_fecha and not fecha_actual:
                    hay_cambio = True

                if nueva_fecha:
                    es_actuacion_reciente = nueva_fecha >= ayer

                if hay_cambio:
                    # Si hay cambio detectado, usamos la funcin maestra para traer todo (actuaciones, sujetos, etc.)
                    try:
                        print(f"   [SYNC] Cambio detectado en {c.radicado}. Sincronizando actuaciones...")
                        await validar_radicado_completo(c.radicado, db, is_new_import=False)
                        updated_cases.append({
                            "radicado": c.radicado,
                            "demandante": c.demandante,
                            "demandado": c.demandado,
                            "juzgado": c.juzgado,
                            "ultima_actuacion": nueva_fecha.isoformat() if nueva_fecha else None,
                        })
                    except Exception as sync_e:
                        print(f"    [ERROR-SYNC] Fall en sincronizacin profunda de {c.radicado}: {sync_e}")
                        # Fallback: al menos actualizamos la fecha para que no intente refrescarlo de inmediato en el siguiente loop
                        c.ultima_actuacion = nueva_fecha
                        c.last_check_at = now_colombia()

                c.last_check_at = now_colombia()
                checked += 1

                if (i + 1) % MINI_BATCH == 0:
                    try:
                        db.commit()
                        print(f"   (OK) Commit parcial: {i+1}/{len(case_ids)} casos")
                    except Exception as e:
                        print(f"   (Warn) Error en commit parcial: {e} - reconectando...")
                        try: db.rollback()
                        except: pass
                        try: db.close()
                        except: pass
                        db = get_fresh_db()

            except Exception as e:
                print(f"   (Error) Error procesando caso_id={case_id}: {e}")
                errors += 1
                if "ssl" in str(e).lower() or "connection" in str(e).lower():
                    try:
                        if db: db.close()
                    except: pass
                    db = get_fresh_db()

        if db:
            try:
                db.commit()
                print(f"    Commit final")
            except Exception as e:
                print(f"    Error en commit final: {e}")
                try: db.rollback()
                except: pass

        if updated_cases:
            _accumulate_and_notify(updated_cases)

        return {
            "ok": True,
            "checked": checked,
            "updated_cases": len(updated_cases),
            "errors": errors,
            "total_in_db": total_cases,
            "cases_with_changes": updated_cases,
        }

    except Exception as e:
        print(f" Error en do_auto_refresh: {e}")
        raise
    finally:
        if db:
            try: db.close()
            except: pass


async def save_new_actuaciones(case: Case, id_proceso: int, db: Session):
    try:
        await asyncio.sleep(random.uniform(0.2, 0.5))
        acts_resp = await actuaciones_proceso(int(id_proceso))
        acts = []
        if isinstance(acts_resp, dict):
            acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
        elif isinstance(acts_resp, list):
            acts = acts_resp

        for a in acts:
            con_docs = bool(a.get("conDocumentos")) if a.get("conDocumentos") is not None else False
            it = {
                "id_reg_actuacion": a.get("idRegActuacion"),
                "cons_actuacion": a.get("consActuacion"),
                "llave_proceso": a.get("llaveProceso"),
                "event_date": a.get("fechaActuacion"),
                "title": (a.get("actuacion") or "").strip(),
                "detail": a.get("anotacion"),
                "fecha_inicio": a.get("fechaInicial"),
                "fecha_fin": a.get("fechaFinal"),
                "fecha_registro": a.get("fechaRegistro"),
                "con_documentos": con_docs,
                "cant": a.get("cant"),
            }
            event_hash = sha256_obj(it)
            exists = db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id,
                CaseEvent.event_hash == event_hash
            ).first()
            if not exists:
                db.add(CaseEvent(
                    case_id=case.id,
                    event_date=it.get("event_date"),
                    title=it.get("title"),
                    detail=it.get("detail"),
                    event_hash=event_hash,
                    con_documentos=con_docs,
                    id_reg_actuacion=it.get("id_reg_actuacion"),
                    cons_actuacion=it.get("cons_actuacion"),
                ))
                if con_docs:
                    case.has_documents = True
    except Exception as e:
        print(f"    Error guardando actuaciones: {e}")


def _accumulate_and_notify(new_cases: List[dict]):
    global _notification_accumulator, _notification_accumulator_date

    hoy = today_colombia()

    if _notification_accumulator_date and _notification_accumulator_date < hoy:
        print(f" Acumulador de {_notification_accumulator_date} descartado  nuevo da")
        _notification_accumulator = []

    _notification_accumulator_date = hoy

    # El acumulador ahora evita duplicar (radicado + juzgado) o (radicado + id_proceso)
    def get_case_key(c_obj):
        return f"{c_obj.get('radicado')}_{c_obj.get('juzgado', '')}"

    llaves_existentes = {get_case_key(c) for c in _notification_accumulator}
    for c in new_cases:
        key = get_case_key(c)
        if key not in llaves_existentes:
            _notification_accumulator.append(c)
            llaves_existentes.add(key)

    total = len(_notification_accumulator)
    hora  = now_colombia().hour

    print(f"[EMAIL] Acumulador: {total} casos | hora={hora}:00")

    should_send = (
        total >= NOTIFICATION_BATCH_SIZE
        or (hora >= NOTIFICATION_FLUSH_HOUR and total > 0)
    )

    if should_send:
        print(f"Enviando correo con {total} casos acumulados...")
        send_grouped_notification(_notification_accumulator)
        _notification_accumulator = []
    else:
        print(f" Acumulando... {total}/{NOTIFICATION_BATCH_SIZE} casos (envo a las {NOTIFICATION_FLUSH_HOUR}:00 si no se llega antes)")


def send_grouped_notification(updated_cases: List[dict]):
    db = SessionLocal()
    try:
        config = db.query(NotificationConfig).first()
        if not config or not config.is_active:
            return
        if not config.smtp_user or not config.smtp_pass or not config.notification_emails:
            return

        emails = [e.strip() for e in (config.notification_emails or "").split(",") if e.strip()]
        if not emails:
            return

        count = len(updated_cases)
        subject = f" {count} caso{'s' if count > 1 else ''} con nuevas actuaciones - EMDECOB"

        log = NotificationLog(
            recipients=", ".join(emails),
            cases_count=count,
            subject=subject,
            status="sent",
        )

        try:
            rows_html = ""
            for case in updated_cases:
                rows_html += f"""
                <tr>
                  <td style="padding:8px;border:1px solid #ddd;font-family:monospace;font-size:12px;">{case.get('radicado', '')}</td>
                  <td style="padding:8px;border:1px solid #ddd;">{case.get('demandante', '') or ''}</td>
                  <td style="padding:8px;border:1px solid #ddd;">{case.get('demandado', '') or ''}</td>
                  <td style="padding:8px;border:1px solid #ddd;font-size:12px;">{case.get('juzgado', '') or ''}</td>
                  <td style="padding:8px;border:1px solid #ddd;text-align:center;">{case.get('ultima_actuacion', '') or ''}</td>
                </tr>
                """

            body = f"""
            <html>
            <body style="font-family:Arial,sans-serif;padding:20px;">
              <h2 style="color:#0d9488;"> Nuevas Actuaciones Detectadas</h2>
              <p>Se han detectado <strong>{count}</strong> caso{'s' if count > 1 else ''} con nuevas actuaciones:</p>

              <table style="border-collapse:collapse;width:100%;margin-top:20px;">
                <thead>
                  <tr style="background:#0d9488;color:white;">
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Radicado</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Demandante</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Demandado</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Juzgado</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:center;">lt. Actuacin</th>
                  </tr>
                </thead>
                <tbody>
                  {rows_html}
                </tbody>
              </table>
              <hr style="margin-top:30px;">
              <p style="color:#888;font-size:12px;">
                Mensaje automtico EMDECOB Consultas<br>
                Fecha: {now_colombia().strftime('%Y-%m-%d %H:%M:%S')}
              </p>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = config.smtp_from or config.smtp_user
            msg["To"] = ", ".join(emails)
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config.smtp_user, config.smtp_pass)
                server.sendmail(msg["From"], emails, msg.as_string())

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)

        db.add(log)
        db.commit()

    finally:
        db.close()


def get_unread_cases_for_notification(db: Session) -> List[dict]:
    hoy = today_colombia()
    ayer = hoy - timedelta(days=1)

    cases = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
        )
    ).order_by(desc(func.substr(Case.radicado, 13, 4)), desc(Case.ultima_actuacion)).all()

    return [
        {
            "radicado": c.radicado,
            "demandante": c.demandante,
            "demandado": c.demandado,
            "juzgado": c.juzgado,
            "ultima_actuacion": c.ultima_actuacion.isoformat() if c.ultima_actuacion else None,
        }
        for c in cases
    ]


async def _pending_validation_loop():
    BATCH = 30
    DELAY_BETWEEN = 2.5
    CYCLE_WAIT = 300

    print("[pending-loop] Loop de validacion de pendientes activo")
    await asyncio.sleep(15)

    while True:
        db = None
        try:
            db = SessionLocal()
            total = db.query(Case).filter(Case.juzgado.is_(None)).count()

            if total > 0:
                print(f" [pending-loop] {total} casos pendientes  validando lote de {min(BATCH, total)}...")
                pendientes = db.query(Case).filter(Case.juzgado.is_(None)).limit(BATCH).all()

                for i, c in enumerate(pendientes):
                    try:
                        if i > 0:
                            await asyncio.sleep(DELAY_BETWEEN + random.uniform(0, 0.8))
                        result = await validar_radicado_completo(c.radicado, db, is_new_import=True)
                        if result["found"]:
                            inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                            if inv:
                                db.delete(inv)
                            print(f"    [pending-loop] Validado: {c.radicado}")
                        else:
                            inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                            if inv:
                                inv.intentos += 1
                                inv.updated_at = now_colombia()
                            else:
                                db.add(InvalidRadicado(radicado=c.radicado, motivo="No encontrado en Rama Judicial", intentos=1))
                            print(f"    [pending-loop] No encontrado (reintentar): {c.radicado}")
                        db.flush()
                    except Exception as e:
                        print(f"    [pending-loop] Error en {c.radicado}: {e}")

                db.commit()
                remaining = db.query(Case).filter(Case.juzgado.is_(None)).count()
                print(f" [pending-loop] Ciclo completo. Restantes: {remaining}")
            else:
                print(" [pending-loop] Sin pendientes. Prxima revisin en 5 min.")

        except Exception as e:
            print(f" [pending-loop] Error en ciclo: {e}")
        finally:
            if db:
                db.close()

        await asyncio.sleep(CYCLE_WAIT)

async def run_publicaciones_worker_loop():
    from backend.models import CasePublicationSearch
    from backend.service.publicaciones import consultar_publicaciones_rango, parse_fecha_pub, guardar_publicacion_validada, guardar_estado_busqueda
    from sqlalchemy import text
    import traceback

    CONCURRENCY = 1
    SLEEP_MS = 0.8
    MAX_RETRIES = 2
    LOCK_TIMEOUT_MINUTES = 15
    BATCH_SIZE = 5

    print("[pub-worker] Iniciando worker automático de publicaciones procesales...")
    await asyncio.sleep(5)  # Esperar a que inicie la app

    while True:
        db = None
        try:
            db = SessionLocal()
            
            # Recuperar tareas colgadas
            timeout_threshold = now_colombia() - timedelta(minutes=LOCK_TIMEOUT_MINUTES)
            colgadas = db.query(CasePublicationSearch).filter(
                CasePublicationSearch.estado == "procesando",
                CasePublicationSearch.locked_at < timeout_threshold
            ).all()
            for c in colgadas:
                c.estado = "pendiente"
                c.estado_busqueda = "pendiente"
                c.locked_at = None
                c.locked_by = None
                c.ultimo_error = "Timeout. Recuperada por el worker."
                c.intentos += 1
            if colgadas:
                db.commit()
                print(f"[pub-worker] Recuperadas {len(colgadas)} tareas colgadas.")

            # Obtener pendientes (Select for update skip locked no está en SQLite, usaremos un update atómico)
            # Primero buscamos candidatos
            candidatos = db.query(CasePublicationSearch).filter(
                CasePublicationSearch.estado == "pendiente",
                or_(CasePublicationSearch.next_retry_at.is_(None), CasePublicationSearch.next_retry_at <= now_colombia())
            ).order_by(desc(CasePublicationSearch.prioridad), CasePublicationSearch.created_at).limit(BATCH_SIZE).all()

            if not candidatos:
                await asyncio.sleep(5.0)
                continue

            for candidato in candidatos:
                # Intento de lock optimista
                locked_id = candidato.id
                worker_id = f"worker_{id(asyncio.current_task())}"
                now_ts = now_colombia()
                
                # Ejecutar UPDATE crudo para el lock
                stmt = text("""
                    UPDATE publicaciones_busquedas 
                    SET estado='procesando', estado_busqueda='procesando', locked_at=:now, locked_by=:worker 
                    WHERE id=:id AND estado='pendiente'
                """)
                res = db.execute(stmt, {"now": now_ts, "worker": worker_id, "id": locked_id})
                db.commit()

                if res.rowcount == 0:
                    continue # Otro worker la tomó
                
                # Refrescar instancia
                db.refresh(candidato)
                print(f"[pub-worker] Procesando ID={candidato.id} Radicado={candidato.radicado} Mes={candidato.mes_busqueda}")
                
                try:
                    fecha_act_str = candidato.fecha_actuacion.strftime("%Y-%m-%d")
                    year, month = map(int, candidato.mes_busqueda.split("-"))
                    
                    # Llamar al scraper real
                    pubs = await consultar_publicaciones_rango(
                        candidato.radicado, 
                        fecha_act_str, 
                        year=year, 
                        month=month
                    )
                    
                    if pubs:
                        for pub_data in pubs:
                            pub_data["radicado"] = candidato.radicado
                            guardar_publicacion_validada(db, pub_data)
                            
                        candidato.estado = "encontrada"
                        candidato.estado_busqueda = "encontrada"
                    else:
                        candidato.estado = "sin_resultado"
                        candidato.estado_busqueda = "sin_resultado"
                        
                    candidato.processed_at = now_colombia()
                    candidato.ultimo_error = None
                    db.commit()
                    
                except Exception as e:
                    db.rollback()
                    err_msg = str(e) + "\n" + traceback.format_exc()
                    candidato.intentos += 1
                    candidato.ultimo_error = err_msg[:500]
                    candidato.processed_at = now_colombia()
                    
                    if candidato.intentos >= MAX_RETRIES and not candidato.force:
                        candidato.estado = "error"
                        candidato.estado_busqueda = "error"
                    else:
                        candidato.estado = "pendiente"
                        candidato.estado_busqueda = "pendiente"
                        candidato.next_retry_at = now_colombia() + timedelta(minutes=5 * candidato.intentos)
                        
                    candidato.locked_at = None
                    candidato.locked_by = None
                    db.add(candidato)
                    db.commit()
                    print(f"[pub-worker] Error ID={candidato.id}: {e}")
                
                # Sleep de protección entre requests a la Rama
                await asyncio.sleep(SLEEP_MS)
                
        except Exception as e:
            print(f"[pub-worker] Error fatal en loop: {e}")
            await asyncio.sleep(5.0)
        finally:
            if db:
                db.close()
                
        await asyncio.sleep(0.1)


# =========================
# LIFESPAN (STARTUP/SHUTDOWN)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global auto_refresh_task, auto_refresh_running, auto_refresh_stats

    print("[START] Iniciando EMDECOB Consultas...")
    # Garantizar que las tablas existan
    Base.metadata.create_all(bind=engine)
    
    # Reparación manual de columnas faltantes para evitar errores 500
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('tasks')]
        with engine.connect() as conn:
            if 'assignee_id' not in cols:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN assignee_id INTEGER REFERENCES users(id)"))
                print("Migración: Columna assignee_id añadida")
            if 'parent_id' not in cols:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN parent_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE"))
                print("Migración: Columna parent_id añadida")
            if 'clickup_id' not in cols:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN clickup_id VARCHAR(100)"))
                print("Migración: Columna clickup_id añadida")
            if 'assignee_name' not in cols:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN assignee_name VARCHAR(200)"))
                print("Migración: Columna assignee_name añadida")
            conn.commit()
            
    except Exception as e:
        print(f"[DB] Error en migraciones de tareas antiguas: {e}")
        
    # --- AUTO-MIGRACIÓN SaaS POSTGRESQL INDEPENDIENTE ---
    try:
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            # --- MIGRACION POSTGRESQL AUTOMATICA DE TODAS LAS TABLAS Y COLUMNAS ---
            try: conn.execute(text("ALTER TABLE task_assignees ADD COLUMN IF NOT EXISTS task_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_assignees ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS radicado VARCHAR(60);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS id_proceso VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS demandante VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS demandado VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS juzgado VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS alias VARCHAR(200);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS cedula VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS abogado VARCHAR(200);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS telefono VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS last_hash VARCHAR(64);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS current_hash VARCHAR(64);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS last_check_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS fecha_radicacion DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS ultima_actuacion DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS has_documents BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS sync_pub_status VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS sync_pub_progress INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT True;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE billing_tiers ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE billing_tiers ADD COLUMN IF NOT EXISTS min_cases INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE billing_tiers ADD COLUMN IF NOT EXISTS max_cases INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE billing_tiers ADD COLUMN IF NOT EXISTS price FLOAT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE billing_tiers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE billing_tiers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS case_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS event_date VARCHAR(60);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS title VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS detail TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS event_hash VARCHAR(64);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS con_documentos BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS id_reg_actuacion BIGINT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS cons_actuacion BIGINT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS documentos_cache TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT True;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS radicado VARCHAR(23);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS motivo VARCHAR(255) DEFAULT 'No encontrado en Rama Judicial';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS intentos INTEGER DEFAULT 1;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS smtp_host VARCHAR(255) DEFAULT 'smtp.gmail.com';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS smtp_port INTEGER DEFAULT 587;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS smtp_user VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS smtp_pass VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS smtp_from VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS notification_emails TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_config ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS recipients TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS subject VARCHAR(500);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS cases_count INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'sent';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS error_message TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS nit VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS estado VARCHAR(50) DEFAULT 'activo';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS limite_usuarios INTEGER DEFAULT 5;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS suspension_reason TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS suspended_by INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS reactivated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS reactivated_by INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'al_dia';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS next_payment_due DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS billing_notes TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS name VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS description VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE permissions ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE permissions ADD COLUMN IF NOT EXISTS name VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS role_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS permission_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE user_roles ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE user_roles ADD COLUMN IF NOT EXISTS role_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT True;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS token_hash VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS used_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS ip_request VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS user_agent TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS case_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS fecha_publicacion DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS tipo_publicacion VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS descripcion TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS documento_url TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS source_url TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS source_id VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS url_fuente_principal TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS tipo_fuente_principal VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS texto_fuente_principal TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS validada_por_fuente_principal BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS numero_estado VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS fecha_estado_electronico DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS url_resumen_publicacion TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS url_cuadro TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS url_providencia TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS documentos_complementarios TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS match_fuerte BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS match_type VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS motivo_match TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS observacion TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS estado_validacion VARCHAR(50) DEFAULT 'requiere_revision';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS match_score INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS texto_bloque_match TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS motivo_descarte TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS fuente_principal_validada BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS requiere_revision BOOLEAN DEFAULT True;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS elementos_detectados TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS documento_nombre TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS extraction_quality VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS validado_manual BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS aprobado_por_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS descartado_manual BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS descartado_por_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS discarded_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS observacion_revision TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE case_publications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS accion VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entidad VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entidad_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS metadata_json TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS radicado VARCHAR(60);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS fecha_actuacion DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS fecha_inicio_busqueda DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS fecha_fin_busqueda DATE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS despacho_codigo VARCHAR(20);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS estado VARCHAR(50) DEFAULT 'pendiente';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS estado_busqueda VARCHAR(50) DEFAULT 'pendiente';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS fecha_ultima_busqueda TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS intento_manual BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS error TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS debug TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS mes_busqueda VARCHAR(20);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS prioridad INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS intentos INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS ultimo_error TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS locked_by VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS force BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS source_trigger VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS total_items INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS processed_items INTEGER DEFAULT 0;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS is_imported BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS results_json TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS error_message TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE search_jobs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS name VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS description TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS visibility VARCHAR(50) DEFAULT 'TEAM_COLLABORATION';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS owner_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspace_members ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspace_members ADD COLUMN IF NOT EXISTS workspace_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspace_members ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE workspace_members ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'VIEWER';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE folders ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE folders ADD COLUMN IF NOT EXISTS name VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE folders ADD COLUMN IF NOT EXISTS workspace_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE folders ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE folders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS name VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS folder_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS workspace_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_tags ADD COLUMN IF NOT EXISTS task_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_tags ADD COLUMN IF NOT EXISTS tag_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tags ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tags ADD COLUMN IF NOT EXISTS name VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tags ADD COLUMN IF NOT EXISTS color VARCHAR(50) DEFAULT '#3b82f6';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS title VARCHAR(500);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS description TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'To Do';"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR(50);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_date TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS list_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS creator_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS case_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS parent_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_name VARCHAR(200);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS custom_fields TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS task_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS content TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS user_name VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_checklist_items ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_checklist_items ADD COLUMN IF NOT EXISTS task_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_checklist_items ADD COLUMN IF NOT EXISTS content VARCHAR(500);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_checklist_items ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT False;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_checklist_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_attachments ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_attachments ADD COLUMN IF NOT EXISTS task_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_attachments ADD COLUMN IF NOT EXISTS name VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_attachments ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_attachments ADD COLUMN IF NOT EXISTS file_type VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE task_attachments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS service_name VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS api_key VARCHAR(255);"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT True;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS settings TEXT;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            try: conn.execute(text("ALTER TABLE integration_config ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;"))
            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')
            tables_to_add = ["case_events", "case_publications", "tasks", "search_jobs", "workspaces", "invalid_radicados"]
            for t in tables_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS company_id INTEGER"))
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{t}_company_id ON {t}(company_id)"))
                    conn.commit()
                except Exception as ex:
                    conn.rollback() # Limpiar transaction state si falla (ej. en local/sqlite)
                    pass
            
            # Crear empresa CODE si no existe dinámicamente sin ID fijo
            conn.execute(text("INSERT INTO companies (nombre, estado) SELECT 'CODE', 'activo' WHERE NOT EXISTS (SELECT 1 FROM companies WHERE upper(nombre) = 'CODE' OR upper(nombre) = 'EMDECOB')"))
            conn.commit()
            
            # Obtener CODE_ID real
            res = conn.execute(text("SELECT id FROM companies WHERE upper(nombre) = 'CODE' OR upper(nombre) = 'EMDECOB' ORDER BY id LIMIT 1")).fetchone()
            code_id = res[0] if res else 1
            
            # Asegurar Superadmin
            conn.execute(text(f"UPDATE users SET company_id = {code_id} WHERE company_id IS NULL AND username != 'superadmin'"))
            conn.execute(text("UPDATE users SET company_id = NULL WHERE username = 'superadmin'"))
            
            # Limpiar dato de prueba
            conn.execute(text("DELETE FROM case_events WHERE title LIKE '%Auto de prueba%'"))
            
            # Reparación estricta de orphans pedida por el usuario
            try:
                conn.execute(text("""
                    UPDATE case_events ce 
                    SET company_id = c.company_id 
                    FROM cases c 
                    WHERE ce.case_id = c.id AND ce.company_id IS NULL AND c.company_id IS NOT NULL
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE case_events ce 
                    SET company_id = c.company_id 
                    FROM cases c 
                    WHERE ce.radicado = c.radicado AND ce.company_id IS NULL AND c.company_id IS NOT NULL
                """))
                conn.commit()
            except Exception:
                conn.rollback()

            # Migrar huérfanos restantes a CODE_ID
            tables_to_update = ["cases", "case_events", "case_publications", "publicaciones_busquedas", "tasks", "search_jobs", "workspaces", "invalid_radicados", "audit_logs"]
            for t in tables_to_update:
                try:
                    conn.execute(text(f"UPDATE {t} SET company_id = {code_id} WHERE company_id IS NULL"))
                    conn.commit()
                except Exception:
                    conn.rollback()
                    pass
            
                print(f"[MIGRACION] Auto-SaaS completado para CODE_ID = {code_id}")
    except Exception as e:
        print(f"[DB] Error fatal en Auto-SaaS: {e}")
            
    try:
        with engine.connect() as conn:
            cols_pub = [c['name'] for c in inspector.get_columns('publicaciones_busquedas')]
            if 'mes_busqueda' not in cols_pub:
                print("Migración: Añadiendo columnas de cola a publicaciones_busquedas")
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN mes_busqueda VARCHAR(20)"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN prioridad INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN intentos INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN ultimo_error TEXT"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN processed_at TIMESTAMP"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN locked_at TIMESTAMP"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN locked_by VARCHAR(100)"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN next_retry_at TIMESTAMP"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN force BOOLEAN DEFAULT FALSE"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD COLUMN source_trigger VARCHAR(100)"))
            
            cols_pub_case = [c['name'] for c in inspector.get_columns('case_publications')]
            if 'estado_validacion' not in cols_pub_case:
                print("Migración: Añadiendo columnas de validación a case_publications")
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN estado_validacion VARCHAR(50) DEFAULT 'requiere_revision'"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN match_score INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN texto_bloque_match TEXT"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN motivo_descarte TEXT"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN fuente_principal_validada BOOLEAN DEFAULT FALSE"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN requiere_revision BOOLEAN DEFAULT TRUE"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN elementos_detectados TEXT"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN documento_nombre TEXT"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN extraction_quality VARCHAR(50)"))
                conn.execute(text("ALTER TABLE case_publications ADD COLUMN validated_at TIMESTAMP"))

            # Garantizar tablas de soporte
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS task_checklist_items (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    content VARCHAR(500) NOT NULL,
                    is_completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    except Exception as e:
        print(f"Error en migración rápida: {e}")
        
    _ensure_default_user()
    
    # DIAGNOSTICO DE DATOS
    with SessionLocal() as db:
        try:
            total_cases = db.query(Case).count()
            total_tasks = db.query(Task).count()
            print(f"[DB] Casos en DB: {total_cases}, Tareas: {total_tasks}")
            
            for u in db.query(User).all():
                c_count = db.query(Case).filter(Case.user_id == u.id).count()
                print(f"[DB] Usuario '{u.username}' (ID: {u.id}) -> {c_count} casos")
                
            orphans = db.query(Case).filter(Case.user_id.is_(None)).count()
            print(f"[DB] Casos sin dueo (NULL): {orphans}")
        except Exception as e:
            print(f"[DB] Error en diagnostico: {e}")

    asyncio.create_task(notification_flush_loop())
    print("[EMAIL] Flush loop de notificaciones iniciado")

    auto_refresh_running = True
    auto_refresh_stats["running"] = True
    auto_refresh_task = asyncio.create_task(auto_refresh_loop())
    print(f"[RELOJ] Auto-refresh iniciado (cada {auto_refresh_stats['interval_minutes']} minutos)")

    asyncio.create_task(_pending_validation_loop())
    print("[SYNC] Validacion continua de pendientes iniciada")

    asyncio.create_task(run_publicaciones_worker_loop())
    print("[SYNC] Worker de publicaciones automático iniciado")

    yield

    print(" Deteniendo EMDECOB Consultas...")
    auto_refresh_running = False
    auto_refresh_stats["running"] = False
    if auto_refresh_task:
        auto_refresh_task.cancel()
        try:
            await auto_refresh_task
        except asyncio.CancelledError:
            pass


# =========================
# APP
# =========================
app = FastAPI(
    title="EMDECOB Consultas",
    description="Plataforma interna para consulta y monitoreo de procesos judiciales",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

try:
    from backend.routers import admin
    app.include_router(admin.router)
except Exception as e:
    print("No se pudo cargar el router admin:", e)

# =========================
# SCHEMAS
# =========================
class NotificationConfigUpdate(BaseModel):
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_from: Optional[str] = None
    notification_emails: Optional[str] = None
    is_active: Optional[bool] = False

class TestEmailRequest(BaseModel):
    email: str

class MarkReadBulkRequest(BaseModel):
    case_ids: List[int]

class MarkReadAllRequest(BaseModel):
    search: Optional[str] = None
    juzgado: Optional[str] = None
    solo_no_leidos: bool = False
    solo_actualizados_hoy: bool = False

class ValidateSelectedRequest(BaseModel):
    radicados: List[str]

class AutoRefreshConfigRequest(BaseModel):
    interval_minutes: int = 60

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    nombre: Optional[str] = None
    is_admin: bool = False

class UserUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


from cryptography.fernet import Fernet
import base64
import json

# =========================
# AUTH  Stateless Tokens
# =========================
SECRET_KEY_DEV = base64.urlsafe_b64encode(b'emdecob_secret_jwt_key_123456789')
fernet = Fernet(SECRET_KEY_DEV)

def create_access_token(user_id: int) -> str:
    payload = json.dumps({"user_id": user_id}).encode('utf-8')
    return fernet.encrypt(payload).decode('utf-8')

def verify_access_token(token: str) -> Optional[int]:
    try:
        payload = fernet.decrypt(token.encode('utf-8'), ttl=86400).decode('utf-8')
        data = json.loads(payload)
        return data.get("user_id")
    except Exception as e:
        print(f"[AUTH-DEBUG] Error validando token: {e}")
        return None

bearer_scheme = HTTPBearer(auto_error=False)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# =========================
# USUARIOS HARDCODEADOS (fallback si la BD falla)
# =========================
HARDCODED_USERS = {
    "admin": {
        "password": "Margarita1393$%",
        "id": 9999,
        "nombre": "Administrador",
        "is_admin": True,
    },
    "fna_juridica": {
        "password": "juridicaEmdecob2026$",
        "id": 1,
        "nombre": "FNA Juridica",
        "is_admin": False,
    },
    "fna.juridica": {
        "password": "juridicaEmdecob2026$",
        "id": 1,
        "nombre": "FNA Juridica",
        "is_admin": False,
    },
    "jurico_emdecob": {
        "password": "emdecob2027$",
        "id": 2,
        "nombre": "Juridico Emdecob",
        "is_admin": False,
    },
    "jurico.emdecob": {
        "password": "emdecob2027$",
        "id": 2,
        "nombre": "Juridico Emdecob",
        "is_admin": False,
    },
    "juricob": {
        "password": "emdecob2027$",
        "id": 2,
        "nombre": "Juridico Emdecob",
        "is_admin": False,
    },
    "superadmin": {
        "password": "admin123$",
        "id": 35,
        "nombre": "Super Administrador",
        "is_admin": True,
    },
}


# =========================
# DB
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# AUTH  LOGIN / LOGOUT / USUARIOS
# =========================

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db),
    token: Optional[str] = Query(None)
) -> User:
    try:
        actual_token = None
        if credentials:
            actual_token = credentials.credentials
        elif token:
            actual_token = token
        
        if not actual_token:
            raise HTTPException(status_code=401, detail="No autenticado")
        
        user_id = verify_access_token(actual_token)
        if not user_id:
            print("[AUTH-DEBUG] El token no pudo ser verificado")
            raise HTTPException(status_code=401, detail="Token invalido o expirado")

        print(f"[AUTH-DEBUG] Token valido. UserID: {user_id}")

        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            print(f"[AUTH-DEBUG] Usuario ID {user_id} no encontrado en BD")
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        # Validar suspensión de la empresa (Excepto Superadmin)
        if user.company_id is not None and user.company:
            if user.company.estado in ["suspendida_pago", "inactiva", "vencida"]:
                raise HTTPException(status_code=403, detail="Tu empresa se encuentra suspendida. Por favor contacta al administrador.")

        return user
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=400, detail=f"AUTH ERROR: {str(e)} | TRACE: {traceback.format_exc()}")

def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin and current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Requiere privilegios de SuperAdmin.")
    return current_user

def _ensure_default_user():
    db = SessionLocal()
    try:
        u1 = db.query(User).filter(User.username == "fna_juridica").first()
        if not u1:
            print("[DB] Creando usuario fna_juridica por defecto...")
            db.add(User(
                username="fna_juridica",
                hashed_password=_hash_password("juridicaEmdecob2026$"),
                nombre="FNA Juridica",
                is_active=True,
                is_admin=False,
            ))
            db.commit()
        
        u2 = db.query(User).filter(User.username.in_(["jurico_emdecob", "juricob"])).first()
        if not u2:
            print("[DB] Creando usuario jurico_emdecob por defecto...")
            db.add(User(
                username="jurico_emdecob",
                hashed_password=_hash_password("emdecob2027$"),
                nombre="Juridico Emdecob",
                is_active=True,
                is_admin=False,
            ))
            db.commit()

        # Automate assignment of orphan cases to fna_juridica
        fna_user = db.query(User).filter(User.username == "fna_juridica").first()
        if fna_user:
            orphan_count = db.query(Case).filter(Case.user_id == None).count()
            if orphan_count > 0:
                db.query(Case).filter(Case.user_id == None).update({Case.user_id: fna_user.id})
                db.commit()
                print(f" [DB-SYNC] {orphan_count} casos huerfanos asignados a fna_juridica")
        
        total_cases = db.query(Case).count()
        print(f" [DB-INFO] Total casos en BD: {total_cases}")

    except Exception as e:
        print(f" Error creando usuario por defecto: {e}")
    finally:
        db.close()





# =========================
# HELPERS
# =========================
def clean_str(x):
    if x is None:
        return None
    s = str(x).strip()
    if not s or s.lower() == "nan":
        return None
    return s

def sha256_obj(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _normalizar_nombre(nombre: str) -> Optional[str]:
    if not nombre:
        return None
    n = nombre.strip().upper()
    return n if n else None

_FNA_KEYWORDS = {"FONDO NACIONAL DEL AHORRO", "FNA", "FONDO NAL DEL AHORRO", "F.N.A.", "TRIADA", "FONDO NACIONAL DEL AHORRO - FNA"}

def _es_fna(nombre: str) -> bool:
    if not nombre: return False
    n = nombre.upper()
    return any(kw in n for kw in _FNA_KEYWORDS)

def _asignar_roles_inteligente(nombre_a: Optional[str], nombre_b: Optional[str]):
    if nombre_a and _es_fna(nombre_a):
        return nombre_a, nombre_b
    if nombre_b and _es_fna(nombre_b):
        return nombre_b, nombre_a
    return nombre_a, nombre_b


def parse_sujetos_procesales(sujetos):
    if not sujetos:
        return None, None, None

    demandante = None
    demandado = None
    abogado = None

    if isinstance(sujetos, list):
        ROLES_DEMANDANTE = {"demandante", "accionante", "demandante/accionante", "accionante/demandante", "ejecutante"}
        ROLES_DEMANDADO  = {"demandado", "accionado", "demandado/accionado", "ejecutado", "deudor"}
        ROLES_ABOGADO    = {"defensor privado", "apoderado", "abogado"}
        
        for suj in sujetos:
            if not isinstance(suj, dict):
                continue
            tipo = (suj.get("tipoSujeto") or suj.get("tipo") or "").strip().lower()
            nombre = _normalizar_nombre(suj.get("nombre") or suj.get("name") or "")
            if not nombre:
                continue
            
            if tipo in ROLES_DEMANDANTE and demandante is None:
                demandante = nombre
            elif tipo in ROLES_DEMANDADO and demandado is None:
                demandado = nombre
            elif tipo in ROLES_ABOGADO and abogado is None:
                abogado = nombre
                
        demandante, demandado = _asignar_roles_inteligente(demandante, demandado)
        return demandante, demandado, abogado

    if not isinstance(sujetos, str):
        try:
            sujetos = str(sujetos)
        except Exception:
            return None, None, None

    # Regex para Demandante
    dem_match = re.search(
        r"(?:Demandante(?:[/\-]\w+)?|Accionante|Ejecutante)\s*:\s*([^|]+)",
        sujetos, re.IGNORECASE
    )
    if dem_match:
        demandante = _normalizar_nombre(dem_match.group(1))

    # Regex para Demandado
    ddo_match = re.search(
        r"(?:Demandado(?:[/\-]\w+)?|Accionado|Ejecutado|Deudor)\s*:\s*([^|]+)",
        sujetos, re.IGNORECASE
    )
    if ddo_match:
        demandado = _normalizar_nombre(ddo_match.group(1))
        
    # Regex para Defensor / Abogado
    abo_match = re.search(
        r"(?:Defensor Privado|Apoderado|Abogado)\s*:\s*([^|]+)",
        sujetos, re.IGNORECASE
    )
    if abo_match:
        abogado = _normalizar_nombre(abo_match.group(1))

    demandante, demandado = _asignar_roles_inteligente(demandante, demandado)
    return demandante, demandado, abogado

@app.get("/users", response_model=List[UserOut])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna todos los usuarios activos del sistema para asignaci?n de tareas."""
    return db.query(User).filter(User.is_active == True).all()

def parse_fecha(fecha_str: Optional[str]) -> Optional[date]:
    if not fecha_str:
        return None
    try:
        return datetime.strptime(str(fecha_str)[:10], "%Y-%m-%d").date()
    except:
        return None

def extract_items(resp):
    items = None
    if isinstance(resp, dict):
        items = resp.get("procesos") or resp.get("Procesos") or resp.get("items")
    if not items and isinstance(resp, list):
        items = resp
    if not items or not isinstance(items, list):
        return []
    return items

def extract_fecha_proceso(p: dict, det: Optional[dict]) -> Tuple[Optional[str], Optional[str]]:
    # Priorizar detalle (det) sobre bsqueda (p)
    f_rad = None
    f_ult = None
    
    if det and isinstance(det, dict):
        f_rad = (
            det.get("fechaRadicacion")
            or det.get("fechaProceso")
            or det.get("FechaProceso")
            or det.get("FechaRadicacion")
            or det.get("fechaProcesoRadicacion")
        )
        f_ult = (
            det.get("fechaUltimaActuacion")
            or det.get("FechaUltimaActuacion")
            or det.get("ultimaActuacion")
            or det.get("UltimaActuacion")
        )

    # Fallback a p
    if not f_rad:
        f_rad = (
            p.get("fechaRadicacion")
            or p.get("fechaProceso")
            or p.get("FechaProceso")
            or p.get("FechaRadicacion")
            or p.get("fechaProcesoRadicacion")
        )
    if not f_ult:
        f_ult = (
            p.get("fechaUltimaActuacion")
            or p.get("FechaUltimaActuacion")
            or p.get("ultimaActuacion")
            or p.get("UltimaActuacion")
        )

    return f_rad, f_ult
def extract_juzgado(p: dict, det: Optional[dict]) -> Optional[str]:
    juzgado = None
    if det and isinstance(det, dict):
        juzgado = (
            det.get("despacho")
            or det.get("Despacho")
            or det.get("nombreDespacho")
            or det.get("NombreDespacho")
            or det.get("juzgado")
            or det.get("Juzgado")
        )
    
    if not juzgado:
        juzgado = (
            p.get("despacho")
            or p.get("Despacho")
            or p.get("nombreDespacho")
            or p.get("NombreDespacho")
            or p.get("juzgado")
            or p.get("Juzgado")
        )

    return juzgado

async def obtener_id_proceso(radicado: str) -> Optional[int]:
    # Intentar b?squeda directa
    resp = await consulta_por_radicado(radicado, solo_activos=False, pagina=1)
    items = extract_items(resp)
    
    # Si no hay items, intentar con los primeros 21 d?gitos (por si acaso el final var?a)
    if not items and len(radicado) >= 21:
        print(f"? [rama] Reintentando obtener_id_proceso con 21 d?gitos para {radicado}")
        resp = await consulta_por_radicado(radicado[:21], solo_activos=False, pagina=1)
        items = extract_items(resp)

    if not items:
        return None
        
    p0 = items[0] or {}
    idp = (
        p0.get("idProceso")
        or p0.get("IdProceso")
        or p0.get("id_proceso")
        or p0.get("id")
    )
    try:
        return int(idp) if idp is not None else None
    except:
        return None

def is_unread_case(c: Case) -> bool:
    if not c.current_hash:
        return False
    if c.last_hash:
        return c.current_hash != c.last_hash
    if c.ultima_actuacion:
        hoy = today_colombia()
        ayer = hoy - timedelta(days=1)
        return c.ultima_actuacion >= ayer
    return False

async def delay_between_requests(min_delay: float = 0.3, max_delay: float = 0.6):
    await asyncio.sleep(random.uniform(min_delay, max_delay))


def extract_documentos_from_response(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("documentos", "Documentos", "items", "Items", "data", "Data", "result", "Result"):
            val = raw.get(key)
            if val and isinstance(val, list):
                return val
        if any(k in raw for k in ("idRegistroDocumento", "IdRegistroDocumento", "id", "idDocumento")):
            return [raw]
    return []


async def fetch_documentos_rama_directa(id_reg_actuacion: int, llave_proceso: str = "") -> list:
    iid = int(id_reg_actuacion)

    candidate_paths = [
        f"/Proceso/DocumentosActuacion/{iid}",
        f"/Proceso/Actuacion/Documentos/{iid}",
        f"/Proceso/Actuacion/{iid}/Documentos",
        f"/Proceso/Documento/{iid}",
    ]

    async with httpx.AsyncClient(timeout=30.0, verify=False, headers=RAMA_HEADERS) as client:
        for path in candidate_paths:
            url = f"{RAMA_BASE}{path}"
            print(f"    [fallback] GET {url}")

            try:
                resp = await client.get(url)
                print(f"    [fallback] status={resp.status_code} | body={resp.text[:400]}")

                if resp.status_code in (404, 403, 429):
                    continue
                if resp.status_code != 200:
                    continue

                try:
                    data = resp.json()
                except Exception as e:
                    print(f"    [fallback] Error JSON en {path}: {e}")
                    continue

                docs = extract_documentos_from_response(data)
                if docs:
                    print(f"    [fallback]  {len(docs)} docs en: {path}")
                    return docs

            except Exception as e:
                print(f"    [fallback] Error en {path}: {e}")

    return []


async def validar_radicado_completo(radicado: str, db: Session, is_new_import: bool = False) -> dict:
    try:
        resp = await consulta_por_radicado(radicado, solo_activos=False, pagina=1)
        items = extract_items(resp)
    except RamaError:
        items = []

    if not items:
        return {"found": False, "case": None}

    p = items[0] or {}
    id_proceso = p.get("idProceso") or p.get("IdProceso")

    det = {}
    if id_proceso:
        try:
            await delay_between_requests(0.1, 0.3)
            det = await detalle_proceso(int(id_proceso))
        except:
            det = {}

    sujetos = p.get("sujetosProcesales") or ""
    if not sujetos and det:
        sujetos = det.get("sujetosProcesales") or ""
        
    d1, d2, ab_rama = parse_sujetos_procesales(sujetos)
    juzgado = extract_juzgado(p, det) or "JUZGADO NO ESPECIFICADO"
    fecha_proceso_str, fecha_ult_str = extract_fecha_proceso(p, det)

    new_hash = sha256_obj({"proceso": p, "detalle": det})

    c = db.query(Case).filter(Case.radicado == radicado).first()
    is_new_case = False
    if not c:
        c = Case(radicado=radicado)
        db.add(c)
        db.flush()
        is_new_case = True

    c.demandante = d1
    c.demandado = d2
    c.juzgado = juzgado
    c.id_proceso = str(id_proceso) if id_proceso else None
    c.fecha_radicacion = parse_fecha(fecha_proceso_str)
    c.ultima_actuacion = parse_fecha(fecha_ult_str)
    c.current_hash = new_hash
    c.last_check_at = now_colombia()

    if is_new_case or is_new_import:
        hoy = today_colombia()
        ayer = hoy - timedelta(days=1)
        fecha_ult = parse_fecha(fecha_ult_str)

        if fecha_ult and fecha_ult >= ayer:
            pass
        else:
            c.last_hash = new_hash

    db.flush()

    if id_proceso:
        print(f"[main.py] Obteniendo actuaciones para id_proceso={id_proceso}...")
        try:
            await delay_between_requests(0.1, 0.3)
            acts_resp = await actuaciones_proceso(int(id_proceso))
            acts = []
            if isinstance(acts_resp, dict):
                acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
            elif isinstance(acts_resp, list):
                acts = acts_resp
            
            print(f"[main.py] Procesando {len(acts)} actuaciones...")
            added_count = 0
            for a in acts:
                con_docs = bool(a.get("conDocumentos")) if a.get("conDocumentos") is not None else False
                it = {
                    "id_reg_actuacion": a.get("idRegActuacion"),
                    "cons_actuacion": a.get("consActuacion"),
                    "llave_proceso": a.get("llaveProceso"),
                    "event_date": a.get("fechaActuacion"),
                    "title": (a.get("actuacion") or "").strip(),
                    "detail": a.get("anotacion"),
                    "fecha_inicio": a.get("fechaInicial"),
                    "fecha_fin": a.get("fechaFinal"),
                    "fecha_registro": a.get("fechaRegistro"),
                    "con_documentos": con_docs,
                    "cant": a.get("cant"),
                }
                event_hash = sha256_obj(it)
                exists = db.query(CaseEvent).filter(
                    CaseEvent.case_id == c.id,
                    CaseEvent.event_hash == event_hash
                ).first()
                if not exists:
                    db.add(CaseEvent(
                        case_id=c.id,
                        event_date=it.get("event_date"),
                        title=it.get("title"),
                        detail=it.get("detail"),
                        event_hash=event_hash,
                        con_documentos=con_docs,
                    ))
                    added_count += 1
                    if con_docs:
                        c.has_documents = True
            
            if added_count > 0:
                print(f"[main.py] OK: Se agregaron {added_count} actuaciones nuevas a {c.radicado}")
            else:
                print(f"[main.py] INFO: No hubo actuaciones nuevas (o ya existan) para {c.radicado}")
        except Exception as e:
            print(f"    Error actuaciones: {e}")

    return {"found": True, "case": c}


# =========================
# HOME Y DIAGNOSTICO
# =========================
@app.get("/api/saas-diagnostic")
def saas_diagnostic(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        diag = {}
        # 1. Base de datos conectada (ocultando password)
        url = str(engine.url)
        diag["connection"] = {
            "driver": engine.url.drivername,
            "user": engine.url.username,
            "host": engine.url.host,
            "database": engine.url.database
        }
        
        # 2. Diagnóstico de columnas en tasks
        res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks' ORDER BY ordinal_position")).fetchall()
        diag["tasks_columns"] = [r[0] for r in res]
        
        # 3. Identificar CODE_ID y Superadmin
        code = db.execute(text("SELECT id, nombre FROM companies WHERE upper(nombre) = 'CODE' OR upper(nombre) = 'EMDECOB' LIMIT 1")).fetchone()
        diag["code_company"] = {"id": code[0], "name": code[1]} if code else None
        
        superadmin = db.execute(text("SELECT id, username, company_id FROM users WHERE username = 'superadmin'")).fetchone()
        diag["superadmin"] = {"id": superadmin[0], "username": superadmin[1], "company_id": superadmin[2]} if superadmin else None
        
        # 4. Estado de las tablas operativas
        tables = ["users", "cases", "tasks", "case_events", "case_publications", "publicaciones_busquedas", "search_jobs", "invalid_radicados", "workspaces"]
        table_stats = {}
        for t in tables:
            try:
                has_col = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}' AND column_name = 'company_id'")).fetchone()
                if has_col:
                    nulls = db.execute(text(f"SELECT COUNT(*) FROM {t} WHERE company_id IS NULL")).fetchone()[0]
                    table_stats[t] = {"exists": True, "has_company_id": True, "null_count": nulls}
                else:
                    table_stats[t] = {"exists": True, "has_company_id": False}
            except Exception:
                table_stats[t] = {"exists": False}
        
        diag["tables"] = table_stats
        
        return {"ok": True, "diagnostic": diag}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/fix-saas-data")
def fix_saas_data(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        # Backup (conceptual via logs/print o guardado si fuera script, en endpoint lo omitimos o advertimos)
        
        # Agregar columnas y crear índices
        tables_to_add = ["case_events", "case_publications", "tasks", "search_jobs", "workspaces", "invalid_radicados"]
        for t in tables_to_add:
            try:
                # begin_nested crea un SAVEPOINT en PostgreSQL para no abortar la transacción principal
                with db.begin_nested():
                    db.execute(text(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS company_id INTEGER"))
                    db.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{t}_company_id ON {t}(company_id)"))
            except Exception:
                pass
                
        db.commit() # Consolidar esquema antes de tocar datos
        
        # 1. Obtener o crear CODE
        code_company = db.query(Company).filter(func.upper(Company.nombre) == 'CODE').first()
        if not code_company:
            # Buscar Emdecob para renombrarlo
            code_company = db.query(Company).filter(func.upper(Company.nombre) == 'EMDECOB').first()
            if code_company:
                code_company.nombre = 'CODE'
            else:
                code_company = Company(nombre='CODE', estado='activo')
                db.add(code_company)
            db.commit()
            db.refresh(code_company)
            
        code_id = code_company.id
        
        # 2. Migrar usuarios (Superadmin queda global, el resto a CODE)
        db.execute(text(f"UPDATE users SET company_id = {code_id} WHERE company_id IS NULL AND username != 'superadmin'"))
        db.execute(text("UPDATE users SET company_id = NULL WHERE username = 'superadmin'"))
        
        # 3. Eliminar dato artificial "Auto de prueba (AI)"
        db.execute(text("DELETE FROM case_events WHERE title = 'Auto de prueba (AI)'"))
        db.execute(text("DELETE FROM case_events WHERE title LIKE '%Auto de prueba%'"))
        
        # 4. Asignar CODE a todos los registros huérfanos
        tables_to_update = ["cases", "case_events", "case_publications", "publicaciones_busquedas", "tasks", "search_jobs", "workspaces", "invalid_radicados", "audit_logs"]
        for t in tables_to_update:
            try:
                with db.begin_nested():
                    db.execute(text(f"UPDATE {t} SET company_id = {code_id} WHERE company_id IS NULL"))
            except Exception:
                pass
            
        db.commit()
        return {"ok": True, "message": f"Migración completa. Empresa CODE ID: {code_id}"}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}

@app.get("/api/migrate")
@app.get("/migrate")
async def trigger_real_migration():
    # LANZAMOS LA COPIA REAL EN SEGUNDO PLANO
    asyncio.create_task(run_migration_task())
    return {"ok": True, "message": "MIGRACION INICIADA. Tus 21,000 actuaciones se estan moviendo a juricob. Revisa el Dashboard en 5 minutos."}

async def run_migration_task():
    print("[MIGRACION] Iniciando proceso (Creacion de DB + Copia)...")
    try:
        from backend.create_db import create_database
        create_database()
        
        print("[MIGRACION] Iniciando copia masiva a juricob...")
        # Extraemos la URL completa
        base_url = engine.url.render_as_string(hide_password=False)
        s_url = base_url.replace("juricob", "emdecob_consultas")
        d_url = base_url.replace("emdecob_consultas", "juricob")
        
        s_engine = create_engine(s_url)
        d_engine = create_engine(d_url)
        
        from backend.db import Base
        Base.metadata.create_all(bind=d_engine)
        
        SourceSession = sessionmaker(bind=s_engine)
        DestSession = sessionmaker(bind=d_engine)
        
        with SourceSession() as s_db:
            with DestSession() as d_db:
                # 1. Usuarios
                for u in s_db.query(User).all():
                    if not d_db.query(User).filter(User.username == u.username).first():
                        d_db.merge(u)
                d_db.commit()
                print("[MIGRACION] Usuarios copiados.")

                # 2. Casos
                for c in s_db.query(Case).all():
                    d_db.merge(c)
                d_db.commit()
                print("[MIGRACION] Casos copiados.")
                
                # 3. Actuaciones
                for e in s_db.query(CaseEvent).all():
                    d_db.merge(e)
                d_db.commit()
                print("[MIGRACION] Actuaciones copiadas.")
                
                # 4. Tareas
                for t in s_db.query(Task).all():
                    d_db.merge(t)
                d_db.commit()
                print("[MIGRACION] Tareas copiadas.")
                
        print("[MIGRACION] FINALIZADA CON EXITO.")
    except Exception as e:
        print(f"[MIGRACION] ERROR: {e}")


# =========================
# MONITOR DE ESTADO (Expert)
# =========================
@app.get("/api/status")
@app.get("/status")
def get_migration_status(db: Session = Depends(get_db)):
    try:
        case_count = db.query(Case).count()
        event_count = db.query(CaseEvent).count()
        return {
            "database": "juricob",
            "cases": case_count,
            "events": event_count,
            "status": "VIVO"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/version")
def get_version():
    return {"version": "afc9789f5e68060483ce72910d7b73ab3cada7f0v2", "database": "juricob"}

@app.get("/api/diagnostic/my-cases")
@app.get("/diagnostic/my-cases")
def diagnostic_my_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_jurico = "jurico" in current_user.username.lower() or current_user.id == 2 or current_user.username.lower() == "juricob"
    
    q_all = db.query(Case)
    if is_jurico:
        q_pool = q_all.filter(or_(Case.user_id == current_user.id, Case.user_id == 2))
    else:
        q_pool = q_all.filter(and_(Case.user_id != 2, Case.user_id.isnot(None) if current_user.id != 3 else True))
        
    count_valid = q_pool.filter(Case.juzgado.isnot(None)).count()
    count_pending = q_pool.filter(Case.juzgado.is_(None)).count()
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "is_jurico": is_jurico,
            "is_admin": current_user.is_admin
        },
        "counts": {
            "valid": count_valid,
            "pending": count_pending,
            "total_in_db": db.query(Case).count()
        },
        "database": engine.url.database,
        "host": engine.url.host
    }

@app.get("/")
def read_root():
    return {"status": "ok", "version": "afc9789f5e68060483ce72910d7b73ab3cada7f0", "app": "EMDECOB Consultas"}


# =========================
# STATS
# =========================
@app.get("/api/stats")
@app.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q_validos = db.query(Case).filter(Case.juzgado.isnot(None))
    q_invalidos = db.query(InvalidRadicado)
    q_pendientes = db.query(Case).filter(Case.juzgado.is_(None))

    if current_user.is_admin and not current_user.company_id:
        # SuperAdmin ve TODO sin filtros
        pass
    else:
        # Usuarios ven los casos de su empresa
        q_validos = q_validos.filter(Case.company_id == current_user.company_id)
        q_invalidos = q_invalidos.filter(InvalidRadicado.company_id == current_user.company_id) if hasattr(InvalidRadicado, 'company_id') else q_invalidos
        q_pendientes = q_pendientes.filter(Case.company_id == current_user.company_id)

    total_validos = q_validos.count()
    total_invalidos = q_invalidos.count()
    total_pendientes = q_pendientes.count()
    
    hoy = today_colombia()
    ayer = hoy - timedelta(days=1)

    q_no_leidos = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
        )
    )

    q_hoy = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.ultima_actuacion == hoy,
    )

    if not (current_user.is_admin and not current_user.company_id):
        q_no_leidos = q_no_leidos.filter(Case.company_id == current_user.company_id)
        q_hoy = q_hoy.filter(Case.company_id == current_user.company_id)

    return {
        "total_validos": total_validos,
        "total_pendientes": total_pendientes,
        "total_invalidos": total_invalidos,
        "total_no_leidos": q_no_leidos.count(),
        "total_actualizados_hoy": q_hoy.count(),
        "debug_uid": current_user.id,
    }

@app.get("/api/test-rama-connection")
async def api_test_rama_connection():
    import httpx, time
    url = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2/Proceso/Actuaciones/11001400306720250052600"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://consultaprocesos.ramajudicial.gov.co",
        "Referer": "https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicado"
    }
    start = time.time()
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        elapsed = time.time() - start
        return {
            "environment": "Server",
            "url": url,
            "status_code": resp.status_code,
            "response_time_ms": round(elapsed * 1000, 2),
            "response_headers": dict(resp.headers),
            "response_preview": resp.text[:200] + "..." if len(resp.text) > 200 else resp.text,
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "environment": "Server",
            "url": url,
            "status_code": None,
            "response_time_ms": round(elapsed * 1000, 2),
            "response_headers": None,
            "response_preview": None,
            "error": str(e)
        }


# =========================
# AUTH  LOGIN / LOGOUT / USUARIOS
# =========================

@app.post("/auth/login")
def login(data: LoginRequest):
    """Autentica un usuario y retorna un token de sesi?n."""

    username = data.username.strip()
    
    # 1. Intentar identificaci?n por Hardcoded Users primero para rapidez y resiliencia
    hc = HARDCODED_USERS.get(username)
    
    # 2. Intentar contra la base de datos
    db = None
    user_db = None
    try:
        db = SessionLocal()
        user_db = db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        
        if user_db and _verify_password(data.password, user_db.hashed_password):
            # Validar suspensión de la empresa (Excepto Superadmin)
            if user_db.company_id is not None and user_db.company:
                if user_db.company.estado in ["suspendida_pago", "inactiva", "vencida"]:
                    raise HTTPException(status_code=403, detail="Tu empresa se encuentra suspendida. Por favor contacta al administrador.")
                    
            token = create_access_token(user_db.id)
            return {
                "token": token,
                "access_token": token, # Estándar OAuth2
                "token_type": "bearer",
                "user": {
                    "id": user_db.id,
                    "username": user_db.username,
                    "nombre": user_db.nombre,
                    "is_admin": user_db.is_admin,
                }
            }
    except Exception as e:
        print(f"? [AUTH] Error al consultar DB: {e}. Intentando fallback hardcoded...")
    
    # 3. Fallback Hardcoded si la DB fall? o no encontr? al usuario
    if hc and data.password == hc["password"]:
        # Si el usuario existe en DB, intentamos actualizar su hash (silenciosamente)
        user_id = hc["id"]
        if user_db and db:
            try:
                user_db.hashed_password = _hash_password(data.password)
                db.commit()
                user_id = user_db.id
            except:
                pass
        
        token = create_access_token(user_id)
        return {
            "access_token": token,
            "token": token, # Compatibilidad con el frontend
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": username,
                "is_admin": hc.get("is_admin", False),
                "nombre": hc.get("nombre", username)
            }
        }

    if db:
        db.close()
    
    raise HTTPException(status_code=401, detail="Usuario o contrase?a incorrectos")


@app.post("/auth/logout")
def logout():
    return {"ok": True, "message": "Sesin cerrada"}

@app.post("/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    # 1. Verificar si ya existe
    existing = db.query(User).filter(
        or_(User.username == data.username, User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(400, "El nombre de usuario o correo ya estan registrados")

    # 2. Crear usuario
    new_user = User(
        username=data.username,
        email=data.email,
        nombre=data.nombre,
        hashed_password=_hash_password(data.password),
        is_active=True,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"ok": True, "message": "Usuario registrado exitosamente", "user_id": new_user.id}

@app.post("/auth/register-company")
def register_company(data: RegisterCompanyRequest, db: Session = Depends(get_db)):
    if data.password != data.confirm_password:
        raise HTTPException(400, "Las contraseñas no coinciden")
    
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(400, "El correo ya está registrado")
        
    existing_company = db.query(Company).filter(
        or_(
            Company.nombre.ilike(data.company_name),
            Company.nit == data.company_nit if data.company_nit else False
        )
    ).first()
    
    if existing_company:
        raise HTTPException(400, "La empresa ya se encuentra registrada (mismo nombre o NIT)")
        
    new_company = Company(
        nombre=data.company_name,
        nit=data.company_nit,
        estado=True
    )
    db.add(new_company)
    db.flush()
    
    company_admin_role = db.query(Role).filter(Role.name == "COMPANY_ADMIN").first()
    if not company_admin_role:
        company_admin_role = Role(name="COMPANY_ADMIN", description="Administrador de Empresa")
        db.add(company_admin_role)
        db.flush()
        
    new_user = User(
        username=data.email,
        email=data.email,
        nombre=data.admin_name,
        hashed_password=_hash_password(data.password),
        is_active=True,
        is_admin=False,
        company_id=new_company.id
    )
    new_user.roles.append(company_admin_role)
    db.add(new_user)
    db.commit()
    
    return {"ok": True, "message": "Empresa y usuario creados exitosamente. Ahora puede iniciar sesión."}

@app.post("/api/auth/forgot-password")
@app.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    import hashlib
    user = db.query(User).filter(User.email == data.email).first()
    
    # Generic response
    response_msg = {"success": True, "message": "Si el correo existe, enviaremos instrucciones de recuperación."}
    if not user:
        return response_msg
        
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(reset_token)
    db.commit()
    
    # Send email (mock if no SMTP)
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM_EMAIL", "no-reply@emdecob.com")
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    
    reset_link = f"{frontend_url}/reset-password?token={raw_token}"
    
    if smtp_host and smtp_port:
        import smtplib
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = user.email
        msg['Subject'] = "Recuperación de contraseña"
        body = f"Hola {user.nombre or 'usuario'},\n\nPara recuperar tu contraseña ingresa al siguiente enlace:\n{reset_link}\n\nEste enlace expira en 1 hora."
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        except Exception as e:
            print(f"[SMTP Error] No se pudo enviar correo: {e}")
            # Do not crash, let it return success
    else:
        print(f"[DEV ONLY] Token de recuperación para {user.email}: {reset_link}")
        
    return response_msg

@app.post("/api/auth/reset-password")
@app.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    import hashlib
    if data.new_password != data.confirm_password:
        raise HTTPException(400, "Las contraseñas no coinciden")
        
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None
    ).first()
    
    if not reset_token or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(400, "El token es inválido o ha expirado")
        
    user = reset_token.user
    user.hashed_password = _hash_password(data.new_password)
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    return {"ok": True, "message": "Contraseña actualizada exitosamente"}

@app.post("/auth/change-password")
def change_password(
    data: ChangePasswordRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verificar password actual
    if not _verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(401, "La contraseña actual es incorrecta")

    # 2. Actualizar
    current_user.hashed_password = _hash_password(data.new_password)
    db.commit()

    return {"ok": True, "message": "Contraseña actualizada correctamente"}


@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nombre": current_user.nombre,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
    }


@app.get("/auth/users")
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Permitir que cualquier usuario autenticado vea la lista para asignaciones
    users = db.query(User).order_by(User.created_at).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "nombre": u.nombre,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@app.post("/auth/users")
def create_user(data: UserCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(403, "Solo administradores pueden crear usuarios")
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(400, f"El usuario '{data.username}' ya existe")
    user = User(
        username=data.username,
        hashed_password=_hash_password(data.password),
        nombre=data.nombre,
        is_admin=data.is_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"ok": True, "id": user.id, "username": user.username}


@app.put("/auth/users/{user_id}")
def update_user(user_id: int, data: UserUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(403, "Sin permisos")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if data.nombre is not None:
        user.nombre = data.nombre
    if data.password:
        user.hashed_password = _hash_password(data.password)
    if data.is_active is not None and current_user.is_admin:
        user.is_active = data.is_active
    if data.is_admin is not None and current_user.is_admin:
        user.is_admin = data.is_admin
    db.commit()
    return {"ok": True, "username": user.username}


@app.delete("/auth/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(403, "Solo administradores pueden eliminar usuarios")
    if current_user.id == user_id:
        raise HTTPException(400, "No puedes eliminarte a ti mismo")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    db.delete(user)
    db.commit()
    return {"ok": True}


# =========================
# AUTO-REFRESH STATUS & CONFIG
# =========================
@app.get("/auto-refresh/status")
def get_auto_refresh_status():
    status = dict(auto_refresh_stats)
    status["scheduled_hours"] = "9:00 AM y 3:00 PM (Colombia)"
    status["running"] = auto_refresh_running
    return status

@app.post("/auto-refresh/config")
def set_auto_refresh_config(data: AutoRefreshConfigRequest):
    global auto_refresh_stats
    if data.interval_minutes < 5:
        raise HTTPException(400, "El intervalo mnimo es 5 minutos")
    if data.interval_minutes > 1440:
        raise HTTPException(400, "El intervalo mximo es 1440 minutos (24 horas)")
    auto_refresh_stats["interval_minutes"] = data.interval_minutes
    return {"ok": True, "interval_minutes": data.interval_minutes}

@app.post("/auto-refresh/run-now")
async def run_auto_refresh_now():
    try:
        # 1. Refrescar casos activos
        result = await do_auto_refresh()

        # 2. Validar pendientes (juzgado is None)
        pending_result = {"validated": 0, "not_found": 0}
        try:
            db = SessionLocal()
            pendientes = db.query(Case).filter(Case.juzgado.is_(None)).limit(2).all()
            for i, c in enumerate(pendientes):
                try:
                    if i > 0:
                        await asyncio.sleep(0.5)
                    r = await validar_radicado_completo(c.radicado, db, is_new_import=True)
                    if r["found"]:
                        inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                        if inv:
                            db.delete(inv)
                        pending_result["validated"] += 1
                    else:
                        inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                        if inv:
                            inv.intentos += 1
                            inv.updated_at = now_colombia()
                        else:
                            db.add(InvalidRadicado(radicado=c.radicado, motivo="No encontrado en Rama Judicial", intentos=1))
                        pending_result["not_found"] += 1
                    db.flush()
                except Exception as e:
                    print(f" [cron-pending] Error en {c.radicado}: {e}")
            db.commit()
            db.close()
        except Exception as e:
            print(f" [cron-pending] Error general: {e}")

        # 3. Reintentar no encontrados
        invalid_result = {"found": 0, "still_not_found": 0}
        try:
            db = SessionLocal()
            invalidos = db.query(InvalidRadicado).order_by(InvalidRadicado.updated_at.asc()).limit(2).all()
            for i, item in enumerate(invalidos):
                try:
                    if i > 0:
                        await asyncio.sleep(1.0)
                    r = await validar_radicado_completo(item.radicado, db, is_new_import=True)
                    if r["found"]:
                        db.delete(item)
                        invalid_result["found"] += 1
                    else:
                        item.intentos += 1
                        item.updated_at = now_colombia()
                        invalid_result["still_not_found"] += 1
                    db.flush()
                except Exception as e:
                    print(f" [cron-invalid] Error en {item.radicado}: {e}")
            db.commit()
            db.close()
        except Exception as e:
            print(f" [cron-invalid] Error general: {e}")

        return {
            **result,
            "pending_validated": pending_result["validated"],
            "pending_not_found": pending_result["not_found"],
            "invalid_recovered": invalid_result["found"],
            "invalid_still_pending": invalid_result["still_not_found"],
        }

    except Exception as e:
        raise HTTPException(500, f"Error ejecutando auto-refresh: {str(e)}")

@app.get("/api/documentos/{radicado}/{id_reg_actuacion}")
async def get_docs_actuacion(radicado: str, id_reg_actuacion: int, db: Session = Depends(get_db)):
    try:
        # 1. Intentar obtener desde el caché de la base de datos
        event = db.query(CaseEvent).filter(CaseEvent.id_reg_actuacion == id_reg_actuacion).first()
        if event and event.documentos_cache:
            try:
                cached_data = json.loads(event.documentos_cache)
                return cached_data
            except:
                pass # Si el JSON est corrupto, seguimos con la consulta real

        # 2. Consultar en tiempo real a la Rama Judicial (esto tarda)
        docs = await consultar_documentos(radicado, id_reg_actuacion)
        
        # 3. Guardar en el caché para la próxima vez
        if event and docs:
            event.documentos_cache = json.dumps(docs)
            db.commit()
            
        return docs
    except Exception as e:
        raise HTTPException(500, f"Error al cargar documentos: {str(e)}")


# =========================
# NOTIFICATIONS CONFIG
# =========================
@app.get("/config/notifications")
def get_notification_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Los usuarios registrados pueden ver la config b?sica para que el dashboard no falle
    config = db.query(NotificationConfig).first()

    if not config:
        config = NotificationConfig(smtp_host="smtp.gmail.com", smtp_port=587, is_active=False)
        db.add(config)
        db.commit()
        db.refresh(config)

    return {
        "id": config.id,
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_from": config.smtp_from,
        "notification_emails": config.notification_emails,
        "is_active": config.is_active,
        "has_password": bool(config.smtp_pass),
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }

@app.put("/config/notifications")
def update_notification_config(data: NotificationConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar la configuraci?n")
    config = db.query(NotificationConfig).first()
    if not config:
        config = NotificationConfig()
        db.add(config)

    if data.smtp_host is not None:
        config.smtp_host = data.smtp_host
    if data.smtp_port is not None:
        config.smtp_port = data.smtp_port
    if data.smtp_user is not None:
        config.smtp_user = data.smtp_user
    if data.smtp_pass is not None and data.smtp_pass != "":
        config.smtp_pass = data.smtp_pass
    if data.smtp_from is not None:
        config.smtp_from = data.smtp_from
    if data.notification_emails is not None:
        config.notification_emails = data.notification_emails
    if data.is_active is not None:
        config.is_active = data.is_active

    config.updated_at = now_colombia()
    db.commit()
    return {"ok": True, "message": "Configuracin guardada"}

@app.post("/config/notifications/test")
def test_notification_email(data: TestEmailRequest, db: Session = Depends(get_db)):
    config = db.query(NotificationConfig).first()
    if not config:
        raise HTTPException(400, "No hay configuracin guardada")
    if not config.smtp_user or not config.smtp_pass:
        raise HTTPException(400, "Falta configurar usuario y contrasea SMTP")

    try:
        body = f"""
        <html><body style="font-family:Arial;padding:20px;">
        <h2 style="color:#0d9488;"> Prueba de Notificacin</h2>
        <p>Si recibiste este correo, la configuracin SMTP est correcta.</p>
        <p style="color:#888;font-size:12px;">Fecha: {now_colombia().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body></html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = " Prueba SMTP - EMDECOB Consultas"
        msg["From"] = config.smtp_from or config.smtp_user
        msg["To"] = data.email
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.smtp_user, config.smtp_pass)
            server.sendmail(msg["From"], [data.email], msg.as_string())

        return {"ok": True, "message": "Correo enviado correctamente"}
    except Exception as e:
        raise HTTPException(500, f"Error enviando correo: {str(e)}")

@app.get("/config/notifications/logs")
def get_notification_logs(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    q = db.query(NotificationLog)
    total = q.count()
    logs = (
        q.order_by(desc(NotificationLog.sent_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": log.id,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "recipients": log.recipients,
                "subject": log.subject,
                "cases_count": log.cases_count,
                "status": log.status,
                "error_message": log.error_message,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@app.post("/config/notifications/send-manual")
def send_manual_notification(db: Session = Depends(get_db)):
    try:
        unread_cases = get_unread_cases_for_notification(db)
        if not unread_cases:
            return {"ok": True, "sent": False, "message": "No hay casos no ledos para enviar", "count": 0}

        send_grouped_notification(unread_cases)
        return {"ok": True, "sent": True, "message": f"Correo enviado con {len(unread_cases)} casos", "count": len(unread_cases)}
    except Exception as e:
        raise HTTPException(500, f"Error enviando correo: {str(e)}")


# =========================
# INVALID RADICADOS
# =========================
@app.get("/invalid-radicados")
def list_invalid_radicados(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
):
    q = db.query(InvalidRadicado)
    if not current_user.is_admin:
        q = q.filter(InvalidRadicado.user_id == current_user.id)

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(InvalidRadicado.radicado.like(s))

    total = q.count()
    items = (
        q.order_by(desc(InvalidRadicado.updated_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": x.id,
                "radicado": x.radicado,
                "motivo": x.motivo,
                "intentos": x.intentos,
                "created_at": x.created_at.isoformat() if x.created_at else None,
                "updated_at": x.updated_at.isoformat() if x.updated_at else None,
            }
            for x in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@app.delete("/invalid-radicados/{radicado_id}")
def delete_invalid_radicado(radicado_id: int, db: Session = Depends(get_db)):
    item = db.query(InvalidRadicado).filter(InvalidRadicado.id == radicado_id).first()
    if not item:
        raise HTTPException(404, "Radicado no encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

@app.get("/invalid-radicados/download")
def download_invalid_radicados_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(InvalidRadicado).order_by(desc(InvalidRadicado.updated_at)).all()

    data = [
        {
            "Radicado": x.radicado,
            "Motivo": x.motivo,
            "Intentos": x.intentos,
            "Fecha Registro": x.created_at.strftime("%Y-%m-%d %H:%M") if x.created_at else "",
            "ltimo Intento": x.updated_at.strftime("%Y-%m-%d %H:%M") if x.updated_at else "",
        }
        for x in items
    ]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="No Encontrados")
    output.seek(0)

    filename = f"radicados_no_encontrados_{now_colombia().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.post("/invalid-radicados/{radicado_id}/retry")
async def retry_invalid_radicado(radicado_id: int, db: Session = Depends(get_db)):
    item = db.query(InvalidRadicado).filter(InvalidRadicado.id == radicado_id).first()
    if not item:
        raise HTTPException(404, "Radicado no encontrado")

    result = await validar_radicado_completo(item.radicado, db, is_new_import=True)
    if result["found"]:
        db.delete(item)
        db.commit()
        return {"ok": True, "found": True, "message": "Radicado encontrado, validado y agregado a casos"}
    else:
        item.intentos += 1
        item.updated_at = now_colombia()
        db.commit()
        return {"ok": True, "found": False, "message": "Radicado sigue sin encontrarse en Rama Judicial"}

@app.post("/invalid-radicados/retry-all")
async def retry_all_invalid_radicados(
    db: Session = Depends(get_db),
    delay_seconds: float = Query(default=0.5, ge=0.1, le=5),
):
    items = db.query(InvalidRadicado).order_by(InvalidRadicado.id).all()
    if not items:
        return {"ok": True, "processed": 0, "found": 0, "still_not_found": 0, "remaining": 0, "message": "No hay radicados para reintentar"}

    found = 0
    still_not_found = 0

    for i, item in enumerate(items):
        try:
            if i > 0:
                await asyncio.sleep(delay_seconds + random.uniform(0, 0.3))

            result = await validar_radicado_completo(item.radicado, db, is_new_import=True)
            if result["found"]:
                db.delete(item)
                db.flush()
                found += 1
            else:
                item.intentos += 1
                item.updated_at = now_colombia()
                still_not_found += 1
        except Exception:
            still_not_found += 1

    db.commit()
    remaining = db.query(InvalidRadicado).count()

    return {
        "ok": True,
        "processed": len(items),
        "found": found,
        "still_not_found": still_not_found,
        "remaining": remaining,
        "message": f"Procesados {len(items)}: {found} validados, {still_not_found} no encontrados. Quedan {remaining}."
    }

@app.post("/invalid-radicados/retry-batch")
async def retry_batch_invalid_radicados(
    db: Session = Depends(get_db),
    batch_size: int = Query(default=20, ge=1, le=100),
):
    items = db.query(InvalidRadicado).order_by(InvalidRadicado.id).limit(batch_size).all()
    if not items:
        return {"ok": True, "processed": 0, "found": 0, "still_not_found": 0, "remaining": 0, "message": "No hay radicados para reintentar"}

    found = 0
    still_not_found = 0

    for i, item in enumerate(items):
        try:
            if i > 0:
                await delay_between_requests(0.3, 0.6)

            result = await validar_radicado_completo(item.radicado, db, is_new_import=True)
            if result["found"]:
                db.delete(item)
                found += 1
            else:
                item.intentos += 1
                item.updated_at = now_colombia()
                still_not_found += 1
        except Exception:
            still_not_found += 1

    db.commit()
    remaining = db.query(InvalidRadicado).count()

    return {
        "ok": True,
        "processed": len(items),
        "found": found,
        "still_not_found": still_not_found,
        "remaining": remaining,
        "message": f"Procesados {len(items)}: {found} validados, {still_not_found} no encontrados. Quedan {remaining}."
    }

@app.delete("/invalid-radicados/delete-all")
def delete_all_invalid_radicados(db: Session = Depends(get_db)):
    count = db.query(InvalidRadicado).count()
    db.query(InvalidRadicado).delete()
    db.commit()
    return {"ok": True, "deleted": count, "message": f"Se eliminaron {count} radicados no encontrados."}


# =========================
# ABOGADOS LIST
# =========================
@app.get("/cases/abogados")
def list_abogados(db: Session = Depends(get_db)):
    """Retorna una lista nica de nombres de abogados para sugerencias en el filtro."""
    results = db.query(Case.abogado).filter(Case.abogado.isnot(None), Case.abogado != "").distinct().all()
    # extraemos el primer elemento de cada tupla y filtramos vacos
    names = sorted([r[0] for r in results if r[0]])
    return names

# =========================
# CASES LIST
# =========================
@app.get("/api/cases/id/{case_id}")
@app.get("/cases/id/{case_id}")
def get_case_by_id_endpoint(case_id: int, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
    return c

@app.get("/api/cases/by-radicado/{radicado}")
@app.get("/cases/by-radicado/{radicado}")
def get_case_by_radicado_endpoint(radicado: str, db: Session = Depends(get_db)):
    r = clean_str(radicado)
    c = db.query(Case).filter(Case.radicado == r).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
    return [c] # El frontend espera una lista para by-radicado

@app.get("/api/cases")
@app.get("/cases")
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(default=None),
    juzgado: Optional[str] = Query(default=None),
    mes_actuacion: Optional[str] = Query(default=None),
    cedula: Optional[str] = Query(default=None),
    abogado: Optional[str] = Query(default=None),
    solo_validos: bool = Query(default=True),
    solo_pendientes: bool = Query(default=False),
    solo_no_leidos: bool = Query(default=False),
    solo_actualizados_hoy: bool = Query(default=False),
    con_documentos: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=2000),
):
    try:
        q = db.query(Case)

        # Multi-tenancy filter: SaaS Isolation
        if current_user.is_admin and not current_user.company_id:
            pass # SuperAdmin ve todo
        else:
            q = q.filter(Case.company_id == current_user.company_id)

        if solo_pendientes:
            q = q.filter(Case.juzgado.is_(None))
        elif solo_validos:
            q = q.filter(Case.juzgado.isnot(None))

        if solo_no_leidos:
            hoy = today_colombia()
            ayer = hoy - timedelta(days=1)
            q = q.filter(
                Case.current_hash.isnot(None),
                or_(
                    and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
                    and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
                )
            )

        if solo_actualizados_hoy:
            q = q.filter(Case.ultima_actuacion == today_colombia())

        if search:
            s = f"%{search.strip()}%"
            q = q.filter(
                or_(Case.radicado.like(s), Case.demandante.like(s), Case.demandado.like(s), Case.alias.like(s))
            )

        if juzgado:
            q = q.filter(Case.juzgado.like(f"%{juzgado.strip()}%"))

        if cedula:
            q = q.filter(Case.cedula.like(f"%{cedula.strip()}%"))

        if abogado:
            q = q.filter(Case.abogado.like(f"%{abogado.strip()}%"))

        if con_documentos is not None:
            q = q.filter(Case.has_documents == con_documentos)

        if mes_actuacion:
            try:
                year, month = mes_actuacion.split("-")
                from sqlalchemy import extract
                q = q.filter(extract('year', Case.ultima_actuacion) == int(year), extract('month', Case.ultima_actuacion) == int(month))
            except:
                pass

        total = q.count()

        hoy_count = today_colombia()
        ayer_count = hoy_count - timedelta(days=1)

        q_unread = db.query(Case).filter(
            Case.juzgado.isnot(None),
            Case.current_hash.isnot(None),
            or_(
                and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
                and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer_count),
            )
        )

        if current_user.is_admin and not current_user.company_id:
            pass
        else:
            q_unread = q_unread.filter(Case.company_id == current_user.company_id)
        
        unread_count = q_unread.count()

        unread_order = sql_case(
            (and_(Case.current_hash.isnot(None), Case.last_hash.isnot(None), Case.current_hash != Case.last_hash), 0),
            (and_(Case.current_hash.isnot(None), Case.last_hash.is_(None), Case.ultima_actuacion >= ayer_count), 0),
            else_=1
        )

        items = (
            q.order_by(
                unread_order,
                desc(Case.ultima_actuacion),
                desc(Case.updated_at)
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        def to_out(c: Case):
            return {
                "id": c.id,
                "radicado": c.radicado,
                "demandante": c.demandante,
                "demandado": c.demandado,
                "juzgado": c.juzgado,
                "alias": c.alias,
                "fecha_radicacion": c.fecha_radicacion.isoformat() if c.fecha_radicacion else None,
                "ultima_actuacion": c.ultima_actuacion.isoformat() if c.ultima_actuacion else None,
                "last_check_at": c.last_check_at.isoformat() if c.last_check_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "unread": is_unread_case(c),
                "has_documents": c.has_documents,
                "cedula": c.cedula,
                "abogado": c.abogado,
                "has_tasks": len(c.tasks) > 0,
            }

        return {
            "items": [to_out(x) for x in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "unread_count": unread_count,
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=400, detail=f"DEBUG ERROR: {str(e)} | TRACE: {traceback.format_exc()}")


# =========================
# CASES DOWNLOAD EXCEL
# =========================
@app.get("/cases/download")
def download_cases_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(default=None),
    juzgado: Optional[str] = Query(default=None),
    cedula: Optional[str] = Query(default=None),
    abogado: Optional[str] = Query(default=None),
    mes_actuacion: Optional[str] = Query(default=None),
    solo_no_leidos: bool = Query(default=False),
    solo_actualizados_hoy: bool = Query(default=False),
):
    # Multi-tenancy filter
    is_jurico = "jurico" in current_user.username.lower() or current_user.id == 2 or current_user.username.lower() == "juricob"
    
    q = db.query(Case).filter(Case.juzgado.isnot(None))

    if is_jurico:
        q = q.filter(or_(Case.user_id == current_user.id, Case.user_id == 2))
    elif not current_user.is_admin:
        q = q.filter(and_(Case.user_id != 2, Case.user_id.isnot(None)))

    if solo_no_leidos:
        q = q.filter(Case.current_hash.isnot(None), Case.last_hash.isnot(None), Case.current_hash != Case.last_hash)

    if solo_actualizados_hoy:
        q = q.filter(Case.ultima_actuacion == today_colombia())

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(or_(Case.radicado.like(s), Case.demandante.like(s), Case.demandado.like(s)))

    if juzgado:
        q = q.filter(Case.juzgado.like(f"%{juzgado.strip()}%"))

    if cedula:
        q = q.filter(Case.cedula.like(f"%{cedula.strip()}%"))

    if abogado:
        q = q.filter(Case.abogado.like(f"%{abogado.strip()}%"))

    if mes_actuacion:
        try:
            year, month = mes_actuacion.split("-")
            from sqlalchemy import extract
            q = q.filter(extract('year', Case.ultima_actuacion) == int(year), extract('month', Case.ultima_actuacion) == int(month))
        except:
            pass

    cases = q.order_by(desc(Case.ultima_actuacion)).all()

    data = [
        {
            "Radicado": c.radicado,
            "Demandante": c.demandante or "",
            "Demandado": c.demandado or "",
            "Cédula": c.cedula or "",
            "Abogado": c.abogado or "",
            "Juzgado": c.juzgado or "",
            "Fecha Radicación": c.fecha_radicacion.isoformat() if c.fecha_radicacion else "",
            "Última Actuación": c.ultima_actuacion.isoformat() if c.ultima_actuacion else "",
            "Última Verificación": c.last_check_at.strftime("%Y-%m-%d %H:%M") if c.last_check_at else "",
            "Estado": "No leído" if is_unread_case(c) else "Leído",
        }
        for c in cases
    ]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Casos")
    output.seek(0)

    filename = f"casos_{now_colombia().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =========================
# DELETE CASE
# =========================
@app.patch("/cases/{case_id}/lawyer")
async def update_case_lawyer(case_id: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c: raise HTTPException(404)
    abogado = data.get("lawyer")
    c.abogado = abogado
    u = db.query(User).filter(User.nombre == abogado).first()
    if u: c.user_id = u.id
    db.commit()
    return {"status": "ok", "abogado": abogado}

@app.patch("/cases/{case_id}/id-proceso")
async def update_case_id_proceso(case_id: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c: raise HTTPException(404)
    id_proceso = data.get("id_proceso")
    c.id_proceso = id_proceso
    db.commit()
    return {"status": "ok", "id_proceso": id_proceso}

@app.delete("/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")

    radicado = c.radicado
    db.query(CaseEvent).filter(CaseEvent.case_id == case_id).delete()
    db.delete(c)
    db.commit()

    return {"ok": True, "message": f"Caso {radicado} eliminado correctamente"}


# =========================
# MARK READ
# =========================
@app.post("/cases/{case_id}/mark-read")
def mark_case_read(case_id: int, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
    c.last_hash = c.current_hash or c.last_hash
    db.commit()
    return {"ok": True, "id": c.id}

@app.post("/cases/mark-read-bulk")
def mark_read_bulk(data: MarkReadBulkRequest, db: Session = Depends(get_db)):
    ids = [int(x) for x in (data.case_ids or [])]
    if not ids:
        raise HTTPException(400, "No se enviaron ids")

    cases = db.query(Case).filter(Case.id.in_(ids)).all()
    updated = 0
    for c in cases:
        if is_unread_case(c):
            c.last_hash = c.current_hash
            updated += 1

    db.commit()
    return {"ok": True, "updated": updated}

@app.post("/cases/mark-read-all")
def mark_read_all(data: MarkReadAllRequest, db: Session = Depends(get_db)):
    q = db.query(Case).filter(Case.juzgado.isnot(None))

    if data.solo_actualizados_hoy:
        q = q.filter(Case.ultima_actuacion == today_colombia())

    if data.search:
        s = f"%{data.search.strip()}%"
        q = q.filter(or_(Case.radicado.like(s), Case.demandante.like(s), Case.demandado.like(s), Case.alias.like(s)))

    if data.juzgado:
        q = q.filter(Case.juzgado.like(f"%{data.juzgado.strip()}%"))

    if data.solo_no_leidos:
        q = q.filter(Case.current_hash.isnot(None), Case.last_hash.isnot(None), Case.current_hash != Case.last_hash)

    cases = q.all()
    updated = 0
    for c in cases:
        if is_unread_case(c):
            c.last_hash = c.current_hash
            updated += 1

    db.commit()
    return {"ok": True, "updated": updated, "total": len(cases)}


# =========================
# VALIDATE PENDIENTES
# =========================
@app.post("/cases/validate-batch")
async def validate_batch(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    batch_size: int = Query(default=10, ge=1, le=50)
):
    """Lanza la validacion en segundo plano y retorna inmediatamente para evitar timeouts."""

    # Count how many are pending for this user
    q = db.query(Case).filter(Case.juzgado.is_(None))
    if not current_user.is_admin:
        q = q.filter(Case.user_id == current_user.id)
    
    pendientes_count = q.count()

    if pendientes_count == 0:
        return {"ok": True, "processed": 0, "validated": 0, "not_found": 0, "remaining": 0, "message": "No hay casos pendientes"}

    # Get the IDs to process (avoid passing db session to background)
    batch_ids = [c.id for c in q.limit(batch_size).all()]

    async def _run_batch(ids):
        _db = SessionLocal()
        validated = 0
        not_found = 0
        try:
            for i, case_id in enumerate(ids):
                c = _db.query(Case).filter(Case.id == case_id).first()
                if not c:
                    continue
                try:
                    if i > 0:
                        await delay_between_requests(0.5, 1.0)
                    result = await validar_radicado_completo(c.radicado, _db, is_new_import=True)
                    if result["found"]:
                        inv = _db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                        if inv:
                            _db.delete(inv)
                        validated += 1
                    else:
                        not_found += 1
                        inv = _db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                        if inv:
                            inv.intentos += 1
                            inv.updated_at = now_colombia()
                        else:
                            _db.add(InvalidRadicado(radicado=c.radicado, motivo="No encontrado en Rama Judicial", intentos=1))
                    _db.flush()
                except Exception as e:
                    print(f"[validate-batch] Error en {c.radicado}: {e}")
            _db.commit()
            print(f"[validate-batch] Lote completado: {validated} validados, {not_found} no encontrados")
        except Exception as e:
            print(f"[validate-batch] Error general: {e}")
        finally:
            _db.close()

    background_tasks.add_task(_run_batch, batch_ids)

    return {
        "ok": True,
        "processed": len(batch_ids),
        "remaining": pendientes_count,
        "message": f"Procesando {len(batch_ids)} casos en segundo plano. Recarga la pagina en 1-2 minutos para ver los resultados."
    }

@app.post("/cases/validate-selected")
async def validate_selected(data: ValidateSelectedRequest, db: Session = Depends(get_db)):
    radicados = [clean_str(r) for r in (data.radicados or []) if clean_str(r)]
    if not radicados:
        raise HTTPException(400, "No se enviaron radicados")

    casos = db.query(Case).filter(Case.radicado.in_(radicados), Case.juzgado.is_(None)).all()
    validated = 0
    not_found = 0

    for i, c in enumerate(casos):
        try:
            if i > 0:
                await delay_between_requests(0.3, 0.6)

            result = await validar_radicado_completo(c.radicado, db, is_new_import=True)

            if result["found"]:
                inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                if inv:
                    db.delete(inv)
                validated += 1
            else:
                not_found += 1
                inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                if inv:
                    inv.intentos += 1
                    inv.updated_at = now_colombia()
                else:
                    db.add(InvalidRadicado(radicado=c.radicado, motivo="No encontrado en Rama Judicial", intentos=1))
        except Exception:
            pass

    db.commit()
    return {"ok": True, "validated": validated, "not_found": not_found, "requested": len(radicados)}


# =========================
# CASE BY RADICADO
# =========================
@app.get("/cases/{case_id}")
async def get_case_by_id(case_id: int, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
        
    return {
        "id": c.id,
        "radicado": c.radicado,
        "id_proceso": c.id_proceso,
        "demandante": c.demandante,
        "demandado": c.demandado,
        "juzgado": c.juzgado,
        "alias": c.alias,
        "fecha_radicacion": c.fecha_radicacion.isoformat() if c.fecha_radicacion else None,
        "ultima_actuacion": c.ultima_actuacion.isoformat() if c.ultima_actuacion else None,
        "last_check_at": c.last_check_at.isoformat() if c.last_check_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "unread": is_unread_case(c),
        "has_documents": c.has_documents,
        "sync_pub_status": c.sync_pub_status,
        "sync_pub_progress": c.sync_pub_progress,
    }

@app.get("/api/cases/id/{case_id}")
@app.get("/cases/id/{case_id}")
async def get_case_by_id_prefixed(case_id: int, db: Session = Depends(get_db)):
    return await get_case_by_id(case_id, db)

@app.get("/api/cases/by-radicado/{radicado}")
@app.get("/cases/by-radicado/{radicado}")
async def get_case_by_radicado(radicado: str, skip_rama: bool = Query(default=False), db: Session = Depends(get_db)):
    try:
        r = clean_str(radicado)
        if not r:
            raise HTTPException(400, "Radicado requerido")

        try:
            if skip_rama:
                resp = {"codigo": 200, "items": []}
            else:
                resp = await consulta_por_radicado(r, solo_activos=False, pagina=1)
        except RamaError as e:
            raise HTTPException(502, f"Error Rama Judicial: {str(e)}")

        items = extract_items(resp)
        if not items and not skip_rama:
            raise HTTPException(404, "Caso no encontrado en Rama Judicial")

        synced_cases = []
        
        for p in items:
            id_proceso = str(p.get("idProceso") or p.get("IdProceso") or "")
            
            det = {}
            if id_proceso:
                try:
                    det = await detalle_proceso(int(id_proceso))
                except:
                    det = {}

            # Buscar por id_proceso si existe, si no por radicado solo si es el nico
            c = None
            if id_proceso:
                c = db.query(Case).filter(Case.id_proceso == id_proceso).first()
            
            # Si no se encontr por ID nico, buscamos por radicado pero siendo precavidos
            if not c:
                # Si hay varios con el mismo radicado sin id_proceso, es ambiguo.
                # Pero si es una base vieja, quizs solo hay uno.
                c = db.query(Case).filter(Case.radicado == r, Case.id_proceso == None).first()

            is_new_case = False
            if not c:
                c = Case(radicado=r, id_proceso=id_proceso)
                db.add(c)
                db.flush()
                is_new_case = True
            elif not c.id_proceso and id_proceso:
                # Actualizar registro legacy con su ID nico
                c.id_proceso = id_proceso

            sujetos = p.get("sujetosProcesales") or ""
            d1, d2, abo = parse_sujetos_procesales(sujetos)

            c.demandante = d1 or c.demandante
            c.demandado = d2 or c.demandado
            # c.abogado = abo or c.abogado (Removido por peticin del usuario)
            c.juzgado = extract_juzgado(p, det) or c.juzgado

            fecha_proceso_str, fecha_ult_str = extract_fecha_proceso(p, det)
            c.fecha_radicacion = parse_fecha(fecha_proceso_str) or c.fecha_radicacion
            c.ultima_actuacion = parse_fecha(fecha_ult_str) or c.ultima_actuacion

            if is_new_case:
                new_hash = sha256_obj({"proceso": p, "detalle": det})
                c.current_hash = new_hash
                c.last_hash = new_hash

            c.last_check_at = now_colombia()
            
            synced_cases.append({
                "id": c.id,
                "radicado": c.radicado,
                "demandante": c.demandante,
                "demandado": c.demandado,
                "juzgado": c.juzgado,
                "alias": c.alias,
                "fecha_radicacion": c.fecha_radicacion.isoformat() if c.fecha_radicacion else None,
                "ultima_actuacion": c.ultima_actuacion.isoformat() if c.ultima_actuacion else None,
                "last_check_at": c.last_check_at.isoformat() if c.last_check_at else None,
                "unread": is_unread_case(c),
                "has_documents": c.has_documents,
                "sync_pub_status": c.sync_pub_status,
                "sync_pub_progress": c.sync_pub_progress,
            })

        # FALLBACK: Si no hay items (porque saltamos rama) buscamos en la DB local
        if not synced_cases and skip_rama:
            db_cases = db.query(Case).filter(Case.radicado == r).all()
            for c_db in db_cases:
                synced_cases.append({
                    "id": c_db.id,
                    "radicado": c_db.radicado,
                    "demandante": c_db.demandante,
                    "demandado": c_db.demandado,
                    "juzgado": c_db.juzgado,
                    "alias": c_db.alias,
                    "fecha_radicacion": c_db.fecha_radicacion.isoformat() if c_db.fecha_radicacion else None,
                    "ultima_actuacion": c_db.ultima_actuacion.isoformat() if c_db.ultima_actuacion else None,
                    "last_check_at": c_db.last_check_at.isoformat() if c_db.last_check_at else None,
                    "unread": is_unread_case(c_db),
                    "has_documents": c_db.has_documents,
                    "sync_pub_status": c_db.sync_pub_status,
                    "sync_pub_progress": c_db.sync_pub_progress,
                })

        if not synced_cases:
             raise HTTPException(404, "Caso no encontrado")

        db.commit()
        
        # Para compatibilidad con el frontend actual si solo hay uno, retornamos ese.
        # Pero mi plan dice que el frontend debe cambiar para manejar listas.
        # Por ahora retorno la lista y ajusto el frontend.
        return synced_cases
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")


async def trigger_publications_sync(case: Case, item_act: dict, db_session: Session):
    """Tarea en segundo plano para sincronizar con el portal de Publicaciones."""
    try:
        from backend.models import CasePublication
        from backend.service.publicaciones import consultar_publicaciones_rango, parse_fecha_pub
        radicado = case.radicado
        fecha_act = item_act.get("event_date") # "YYYY-MM-DD"
        
        pubs = await consultar_publicaciones_rango(radicado, fecha_act, case.demandante or "", case.demandado or "")
        
        if pubs:
            for p in pubs:
                f_pub = parse_fecha_pub(p.get("fecha"))
                exists = db_session.query(CasePublication).filter(
                    CasePublication.case_id == case.id,
                    CasePublication.source_id == p.get("source_id")
                ).first()
                if not exists:
                    f_est = parse_fecha_pub(p.get("fecha_estado_electronico")) if p.get("fecha_estado_electronico") else f_pub
                    db_session.add(CasePublication(
                        case_id=case.id,
                        fecha_publicacion=f_pub,
                        tipo_publicacion=p.get("tipo"),
                        descripcion=p.get("descripcion") or p.get("snippet"),
                        documento_url=p.get("documento_url"),
                        source_url=p.get("source_url"),
                        source_id=p.get("source_id"),
                        url_fuente_principal=p.get("url_fuente_principal"),
                        tipo_fuente_principal=p.get("tipo_fuente_principal"),
                        texto_fuente_principal=p.get("texto_fuente_principal"),
                        validada_por_fuente_principal=p.get("validada_por_fuente_principal", False),
                        numero_estado=p.get("numero_estado"),
                        fecha_estado_electronico=f_est,
                        url_resumen_publicacion=p.get("url_resumen_publicacion"),
                        url_cuadro=p.get("url_cuadro"),
                        url_providencia=p.get("url_providencia"),
                        documentos_complementarios=p.get("documentos_complementarios"),
                        match_fuerte=p.get("match_fuerte", False),
                        match_type=p.get("match_type"),
                        motivo_match=p.get("motivo_match"),
                        observacion=p.get("observacion")
                    ))
            db_session.commit()
            print(f"[sync-pub] {len(pubs)} publicaciones sincronizadas para {radicado}")
    except Exception as e:
        print(f"[sync-pub] Error sincronizando publicaciones: {e}")

@app.get("/cases/by-radicado/{radicado}")
async def get_case_by_radicado_endpoint(
    radicado: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Busca un caso por radicado. Primero en BD local, luego en Rama Judicial.
    Esto alimenta la p?gina de 'Consultar Caso'.
    """
    r = clean_str(radicado)
    if not r:
        raise HTTPException(400, "Radicado inv?lido")

    # Multi-tenancy filter para búsqueda individual
    is_jurico = "jurico" in current_user.username.lower() or current_user.id == 2 or current_user.username == "juricob"

    # 1. Buscar en BD local
    existing_items = db.query(Case).filter(Case.radicado == r).all()
    if existing_items:
        local_results = []
        for c in existing_items:
            # Si es Jurico, ve sus casos. Si es FNA, ve los de FNA.
            visible = False
            if is_jurico:
                if c.user_id == 2 or c.user_id == current_user.id: visible = True
            else:
                # Otros (FNA) solo ven si es explícitamente FNA o no es de Jurico
                if _es_fna(c.demandante or "") or (c.user_id != 2 and c.user_id != 1): visible = True
                if c.user_id == 1: visible = True
            
            if visible:
                local_results.append({
                    "id": c.id,
                    "radicado": c.radicado,
                    "demandante": c.demandante or "?",
                    "demandado": c.demandado or "?",
                    "juzgado": c.juzgado or "?",
                    "fecha_radicacion": c.fecha_radicacion.isoformat() if c.fecha_radicacion else None,
                    "note": "Caso encontrado en el sistema local."
                })
        
        # Ordenar local por fecha m?s reciente
        local_results.sort(key=lambda x: x['fecha_radicacion'] or '', reverse=True)
        if local_results:
            return local_results

    # 2. Si no existe, buscar en Rama Judicial (Live)
    try:
        # B?squeda inicial r?pida (pocos reintentos)
        # Usamos wait_for para asegurar que no se quede pegado m?s de 25s
        resp = await asyncio.wait_for(consulta_por_radicado(r), timeout=25.0)
        items = extract_items(resp)
        if not items:
            raise HTTPException(404, f"No se encontr? el radicado {r} en la Rama Judicial")

        async def fetch_process_data(p):
            id_p = p.get("idProceso")
            det = None
            if id_p:
                try:
                    # Detalle r?pido (1 reintento para velocidad)
                    from backend.service.rama import _get
                    det = await _get(f"/Proceso/Detalle/{id_p}", retries=1)
                except:
                    pass
            
            sujetos_raw = None
            if det:
                sujetos_raw = det.get("sujetosProcesales")
            if not sujetos_raw:
                sujetos_raw = p.get("sujetosProcesales")
                
            dem, ddo, abo = parse_sujetos_procesales(sujetos_raw)
            f_rad, _ = extract_fecha_proceso(p, det)
            
            return {
                "id": 0, # Virtual
                "radicado": r,
                "demandante": dem or "?",
                "demandado": ddo or "?",
                "juzgado": p.get("despacho") or "?",
                "id_proceso": id_p,
                "fecha_radicacion": f_rad,
                "note": "Caso encontrado en tiempo real (En l?nea)."
            }

        # PROCESAMIENTO PARALELO (SENIOR OPTIMIZATION)
        results = await asyncio.gather(*[fetch_process_data(p) for p in items[:15]])
        
        # FILTRO DINÁMICO: Preferir FNA o TRIADA para usuarios FNA, o mostrar todo para Jurico
        filtered_results = results
        if not is_jurico:
            filtered_results = [r for r in results if _es_fna(r.get("demandante", ""))]
            if not filtered_results:
                filtered_results = results
        
        # ORDENAMIENTO: Fecha de radicaci?n m?s reciente primero
        # La fecha de radicaci?n es la que el usuario prefiere como criterio principal
        sorted_results = sorted(filtered_results, key=lambda x: x.get('fecha_radicacion') or '', reverse=True)
        
        return sorted_results

    except asyncio.TimeoutError:
        raise HTTPException(408, "La Rama Judicial est? respondiendo muy lento. Por favor, intenta de nuevo en unos minutos.")
    except RamaError as e:
        raise HTTPException(502, f"Error Rama Judicial: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error interno buscando radicado: {str(e)}")

@app.get("/api/cases/id/{case_id}/events")
@app.get("/cases/id/{case_id}/events")
async def get_events_by_id(
    case_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q_case = db.query(Case).filter(Case.id == case_id)
    if not current_user.is_admin and current_user.company_id:
        q_case = q_case.filter(Case.company_id == current_user.company_id)
        
    c = q_case.first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
    return await events_logic(c, db)

@app.get("/api/cases/by-radicado/{radicado}/events")
@app.get("/cases/by-radicado/{radicado}/events")
@app.get("/api/cases/{radicado}/events")
@app.get("/cases/{radicado}/events")
async def get_events_by_radicado_unified(
    radicado: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    r = clean_str(radicado)
    q_case = db.query(Case)
    if not current_user.is_admin and current_user.company_id:
        q_case = q_case.filter(Case.company_id == current_user.company_id)
        
    # Si es un numero corto, intentarlo como ID por si acaso el frontend se equivoca
    if r.isdigit() and len(r) < 10:
        c = q_case.filter(Case.id == int(r)).first()
        if c: return await events_logic(c, db)
    
    c = q_case.filter(Case.radicado == r).order_by(Case.id.desc()).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
    return await events_logic(c, db)

async def events_logic(c: Case, db: Session):
    """
    LOGICA OPTIMIZADA: 
    1. Retorna datos de la BD local inmediatamente (Ultra-rapido).
    2. Si los datos son viejos (>12h) o no hay, dispara sync en segundo plano.
    """
    try:
        radicado = c.radicado
        
        # 1. Obtener datos locales actuales ordenados por fecha de actuación (más reciente arriba)
        db_events = db.query(CaseEvent).filter(CaseEvent.case_id == c.id).order_by(desc(CaseEvent.event_date), desc(CaseEvent.id)).all()
        
        # 2. Decidir si necesitamos refrescar (siempre en segundo plano para no bloquear)
        needs_refresh = False
        if not db_events:
            needs_refresh = True
        elif not c.last_check_at or (now_colombia() - c.last_check_at).total_seconds() > 43200:
            needs_refresh = True
        else:
            has_missing_docs_ids = any(e.con_documentos and not e.id_reg_actuacion for e in db_events)
            if has_missing_docs_ids:
                needs_refresh = True
            
        if needs_refresh:
            print(f"[SYNC] Disparando actualizacion para {radicado}")
            # Si no hay eventos, lo hacemos Sincrono la primera vez para que el usuario vea algo
            if not db_events:
                await sync_case_events_background(c.id)
                db_events = db.query(CaseEvent).filter(CaseEvent.case_id == c.id).order_by(desc(CaseEvent.event_date), desc(CaseEvent.id)).all()
                if not db_events and c.ultima_actuacion:
                    return {"items": [], "total": 0, "warning": "El proceso tiene fecha de última actuación, pero el historial aún no está cargado o fue bloqueado. Presiona Actualizar para sincronizar."}
                elif not db_events:
                    return {"items": [], "total": 0, "warning": "No fue posible obtener nuevas actuaciones o el proceso no tiene historial registrado."}
            else:
                # Si ya hay datos, el refresh se hace en segundo plano
                asyncio.create_task(sync_case_events_background(c.id))

        # 2b. Disparar búsqueda automática de publicaciones si existen actuaciones relevantes
        has_relevant = any(is_relevant_actuacion(e.title) for e in db_events)
        if has_relevant:
            asyncio.create_task(save_new_publications_task(c.id))

        # 3. Formatear para el frontend
        result_items = []
        for e in db_events:
            result_items.append({
                "id_reg_actuacion": e.id_reg_actuacion,
                "cons_actuacion": e.cons_actuacion,
                "llave_proceso": radicado,
                "event_date": e.event_date,
                "title": e.title,
                "detail": e.detail,
                "con_documentos": e.con_documentos,
            })
            
        return {"items": result_items, "total": len(result_items)}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error procesando actuaciones: {str(e)}")

async def sync_case_events_background(case_id: int):
    """Tarea asincrona para actualizar un caso sin bloquear al usuario."""
    db = SessionLocal()
    try:
        c = db.query(Case).filter(Case.id == case_id).first()
        if not c: return
        
        id_proceso = c.id_proceso
        if not id_proceso:
            id_proceso = await obtener_id_proceso(c.radicado)
            if id_proceso:
                c.id_proceso = str(id_proceso)
                db.flush()
        
        if not id_proceso: return

        acts_resp = await actuaciones_proceso(int(id_proceso))
        acts = []
        if isinstance(acts_resp, dict):
            acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
        elif isinstance(acts_resp, list):
            acts = acts_resp

        if not acts and c.ultima_actuacion:
            print(f"[SYNC] Advertencia: No se obtuvieron actuaciones para {c.radicado} pero tiene ultima_actuacion.")
            # No borramos el historial anterior si falla la respuesta.

        new_count = 0
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
            
            # FALLBACK REFORZADO: Buscar por fecha, título y detalle para evitar duplicidad total
            if not exists:
                exists = db.query(CaseEvent).filter(
                    CaseEvent.case_id == c.id,
                    CaseEvent.event_date == it["event_date"],
                    CaseEvent.title == it["title"],
                    CaseEvent.detail == it["detail"]
                ).first()
                if exists:
                    # Actualizamos el hash al nuevo formato para que el 'if not exists' lo encuentre la próxima vez
                    exists.event_hash = event_hash
            
            if not exists:
                db.add(CaseEvent(
                    case_id=c.id,
                    company_id=c.company_id,
                    event_date=it["event_date"],
                    title=it["title"],
                    detail=it["detail"],
                    event_hash=event_hash,
                    con_documentos=con_docs,
                    id_reg_actuacion=a.get("idRegActuacion"),
                    cons_actuacion=a.get("consActuacion"),
                ))
                
                # AUTOMATIZACIÓN: Si la nueva actuación es relevante, disparar búsqueda de publicaciones
                if is_relevant_actuacion(it["title"]):
                    # Usamos la función local definida más abajo en este mismo archivo
                    asyncio.create_task(save_new_publications_task(c.id))

                if con_docs: c.has_documents = True
                new_count += 1
            else:
                # Si existe pero no tiene los IDs técnicos (caso de migración), los actualizamos
                if con_docs and (not exists.id_reg_actuacion or not exists.cons_actuacion):
                    exists.id_reg_actuacion = a.get("idRegActuacion")
                    exists.cons_actuacion = a.get("consActuacion")
                    exists.con_documentos = True
                    c.has_documents = True
                    new_count += 1
        
        c.last_check_at = now_colombia()
        db.commit()
        if new_count > 0:
            print(f"[BG-SYNC] {new_count} nuevas actuaciones encontradas para {c.radicado}")
    except Exception as e:
        print(f"[BG-SYNC] Error sincronizando {case_id}: {e}")
    finally:
        db.close()

# =========================
# DOWNLOAD EVENTS EXCEL
# =========================
@app.get("/cases/by-radicado/{radicado}/events.xlsx")
async def download_events_xlsx(radicado: str):
    r = clean_str(radicado)
    if not r:
        raise HTTPException(400, "Radicado requerido")

    try:
        id_proceso = await obtener_id_proceso(r)
    except RamaError as e:
        raise HTTPException(502, f"Error Rama Judicial: {str(e)}")

    if not id_proceso:
        raise HTTPException(404, "No se encontr el proceso")

    try:
        acts_resp = await actuaciones_proceso(int(id_proceso))
    except RamaError as e:
        raise HTTPException(502, f"Error obteniendo actuaciones: {str(e)}")

    acts = []
    if isinstance(acts_resp, dict):
        acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
    elif isinstance(acts_resp, list):
        acts = acts_resp

    df = pd.DataFrame([{
        "Radicado": r,
        "FechaActuacion": a.get("fechaActuacion"),
        "Actuacion": a.get("actuacion"),
        "Anotacion": a.get("anotacion"),
        "FechaInicial": a.get("fechaInicial"),
        "FechaFinal": a.get("fechaFinal"),
        "FechaRegistro": a.get("fechaRegistro"),
    } for a in acts])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Actuaciones")
    output.seek(0)

    filename = f"actuaciones_{r[:20]}_{now_colombia().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/cases/id/{case_id}/events.xlsx")
async def download_events_by_id_xlsx(case_id: int, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")

    id_proceso = c.id_proceso
    if not id_proceso:
        # Fallback a buscar por radicado si no tiene ID proceso
        try:
            id_proceso = await obtener_id_proceso(c.radicado)
        except:
            raise HTTPException(404, "ID de proceso no disponible")

    if not id_proceso:
        raise HTTPException(404, "ID de proceso no disponible")

    try:
        acts_resp = await actuaciones_proceso(int(id_proceso))
    except RamaError as e:
        raise HTTPException(502, f"Error obteniendo actuaciones: {str(e)}")

    acts = []
    if isinstance(acts_resp, dict):
        acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
    elif isinstance(acts_resp, list):
        acts = acts_resp

    df = pd.DataFrame([{
        "Radicado": c.radicado,
        "ID_Proceso": id_proceso,
        "Juzgado": c.juzgado,
        "FechaActuacion": a.get("fechaActuacion"),
        "Actuacion": a.get("actuacion"),
        "Anotacion": a.get("anotacion"),
        "FechaInicial": a.get("fechaInicial"),
        "FechaFinal": a.get("fechaFinal"),
        "FechaRegistro": a.get("fechaRegistro"),
    } for a in acts])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Actuaciones")
    output.seek(0)

    filename = f"actuaciones_{c.radicado[:15]}_{id_proceso}_{now_colombia().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =========================
# DOWNLOAD MULTIPLE EVENTS
# =========================
@app.post("/cases/events/download-multiple")
async def download_multiple_events_excel(radicados: List[str] = Body(...), db: Session = Depends(get_db)):
    try:
        MAX_ROWS = 1_000_000
        all_data = []

        for i, rad in enumerate(radicados):
            rad = clean_str(rad)
            if not rad or len(all_data) >= MAX_ROWS:
                continue

            if i > 0:
                await delay_between_requests(0.2, 0.4)

            try:
                id_proceso = await obtener_id_proceso(rad)
                if not id_proceso:
                    continue

                acts_resp = await actuaciones_proceso(int(id_proceso))
                acts = []
                if isinstance(acts_resp, dict):
                    acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
                elif isinstance(acts_resp, list):
                    acts = acts_resp

                if len(all_data) + len(acts) > MAX_ROWS:
                    break

                c = db.query(Case).filter(Case.radicado == rad).first()

                for a in acts:
                    all_data.append({
                        "Radicado": rad,
                        "Demandante": c.demandante if c else "",
                        "Demandado": c.demandado if c else "",
                        "Juzgado": c.juzgado if c else "",
                        "FechaActuacion": a.get("fechaActuacion"),
                        "Actuacion": a.get("actuacion"),
                        "Anotacion": a.get("anotacion"),
                        "FechaInicial": a.get("fechaInicial"),
                        "FechaFinal": a.get("fechaFinal"),
                        "FechaRegistro": a.get("fechaRegistro"),
                    })
            except Exception:
                continue

        if not all_data:
            raise HTTPException(404, "No hay actuaciones para descargar")

        df = pd.DataFrame(all_data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Actuaciones")
        output.seek(0)

        filename = f"actuaciones_multiple_{now_colombia().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error generando Excel: {str(e)}")


# =========================
# BACKGROUND VALIDATE PENDIENTES
# =========================
async def _background_validate_pendientes():
    BATCH = 50
    DELAY = 2.0
    MAX_CYCLES = 20

    print("[BG-VALIDATE] Iniciando validacion automatica de pendientes...")
    for cycle in range(MAX_CYCLES):
        db = None
        try:
            db = SessionLocal()
            pendientes = db.query(Case).filter(Case.juzgado.is_(None)).limit(BATCH).all()
            if not pendientes:
                print(" [bg-validate] Sin pendientes. Fin.")
                break

            print(f" [bg-validate] Ciclo {cycle+1}: {len(pendientes)} casos...")
            for i, c in enumerate(pendientes):
                try:
                    if i > 0:
                        await asyncio.sleep(DELAY + random.uniform(0, 0.8))
                    result = await validar_radicado_completo(c.radicado, db, is_new_import=True)
                    if result["found"]:
                        inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                        if inv:
                            db.delete(inv)
                    else:
                        inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                        if inv:
                            inv.intentos += 1
                            inv.updated_at = now_colombia()
                        else:
                            db.add(InvalidRadicado(radicado=c.radicado, motivo="No encontrado en Rama Judicial", intentos=1))
                    db.flush()
                except Exception as e:
                    print(f"    [bg-validate] Error en {c.radicado}: {e}")
            db.commit()

            remaining = db.query(Case).filter(Case.juzgado.is_(None)).count()
            print(f" [bg-validate] Restantes: {remaining}")
            if remaining == 0:
                break

            await asyncio.sleep(5)

        except Exception as e:
            print(f" [bg-validate] Error ciclo {cycle+1}: {e}")
        finally:
            if db:
                db.close()

    print(" [bg-validate] Validacin automtica finalizada.")


# =========================
# IMPORT EXCEL
# =========================
@app.post("/cases/import-excel")
async def import_excel(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        name = (file.filename or "").lower()
        if not name.endswith((".xlsx", ".xls", ".csv")):
            raise HTTPException(400, "Sube un archivo .xlsx, .xls o .csv")

        content = await file.read()
        if name.endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))

        df.columns = [str(c).strip() for c in df.columns]
        
        # Normalizar nombres de columnas para bsqueda insensible a maysculas
        cols_lower = {c.lower(): c for c in df.columns}
        
        rad_col = next((cols_lower[k] for k in ["radicado", "numero", "proceso"] if k in cols_lower), None)
        ced_col = next((cols_lower[k] for k in ["cedula", "identificacion", "documento"] if k in cols_lower), None)
        abo_col = next((cols_lower[k] for k in ["abogado", "apoderado"] if k in cols_lower), None)

        if not rad_col:
            raise HTTPException(400, "Falta la columna 'Radicado'")

        created = 0
        updated = 0
        skipped = 0
        count = 0

        # Procesamos en lotes MUY pequeos (20) para evitar errores de tamao de SQL
        batch_size = 20

        for _, row in df.iterrows():
            try:
                radicado = clean_str(row.get(rad_col))
                if not radicado:
                    skipped += 1
                    continue
                
                cedula = str(row.get(ced_col)).strip() if ced_col and pd.notna(row.get(ced_col)) else None
                abogado = str(row.get(abo_col)).strip() if abo_col and pd.notna(row.get(abo_col)) else None
                
                if cedula and (cedula.lower() == "nan" or cedula == ""): cedula = None
                if abogado and (abogado.lower() == "nan" or abogado == ""): abogado = None

                # Buscar TODOS los casos con este radicado
                q_case = db.query(Case).filter(Case.radicado == radicado)
                if not current_user.is_admin and current_user.company_id:
                    q_case = q_case.filter(Case.company_id == current_user.company_id)
                existing_cases = q_case.all()
                
                if existing_cases:
                    for c in existing_cases:
                        c.cedula = cedula or c.cedula
                        c.abogado = abogado or c.abogado
                    updated += 1
                else:
                    # Si ya estaba marcado como inválido, lo removemos para que vuelva a intentar validarse
                    existing_invalid = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == radicado).first()
                    if existing_invalid:
                        db.delete(existing_invalid)
                        db.flush()

                    db.add(Case(
                        radicado=radicado, 
                        cedula=cedula, 
                        abogado=abogado, 
                        user_id=current_user.id,
                        company_id=current_user.company_id
                    ))
                    created += 1
                
                count += 1
                if count % batch_size == 0:
                    db.commit()
            except Exception as row_error:
                print(f" Error procesando fila: {row_error}")
                db.rollback()
                skipped += 1

        db.commit()

        if created > 0:
            asyncio.create_task(_background_validate_pendientes())

        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "message": f"Procesados: {created} nuevos, {updated} actualizados."
        }
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        msg = str(e).split('\n')[0] # Solo la primera lnea para no saturar el UI
        raise HTTPException(500, f"Error en importacin: {msg}")


@app.post("/cases/bulk-delete-excel")
async def bulk_delete_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        name = (file.filename or "").lower()
        if not name.endswith((".xlsx", ".xls", ".csv")):
            raise HTTPException(400, "Sube un archivo .xlsx, .xls o .csv")

        content = await file.read()
        if name.endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))

        df.columns = [str(c).strip() for c in df.columns]
        cols_lower = {c.lower(): c for c in df.columns}
        rad_col = next((cols_lower[k] for k in ["radicado", "numero", "proceso"] if k in cols_lower), None)

        if not rad_col:
            raise HTTPException(400, "Falta la columna 'Radicado'")

        deleted_cases = 0
        count = 0
        batch_size = 20

        for _, row in df.iterrows():
            try:
                radicado = clean_str(row.get(rad_col))
                if not radicado:
                    continue

                # Buscar todos los casos con ese radicado
                cases = db.query(Case).filter(Case.radicado == radicado).all()
                for c in cases:
                    db.query(CaseEvent).filter(CaseEvent.case_id == c.id).delete()
                    db.query(CasePublication).filter(CasePublication.case_id == c.id).delete()
                    db.delete(c)
                    deleted_cases += 1
                
                # Tambin limpiar de invalid si est ah
                db.query(InvalidRadicado).filter(InvalidRadicado.radicado == radicado).delete()

                count += 1
                if count % batch_size == 0:
                    db.commit()
            except Exception as row_error:
                print(f" Error eliminando fila: {row_error}")
                db.rollback()

        db.commit()

        return {
            "ok": True,
            "deleted_cases": deleted_cases,
            "message": f"Se eliminaron {deleted_cases} procesos correctamente."
        }
    except Exception as e:
        db.rollback()
        msg = str(e).split('\n')[0]
        raise HTTPException(500, f"Error en eliminacin masiva: {msg}")


# =========================
# REFRESH ALL (MANUAL)
# =========================
@app.post("/cases/refresh-all")
async def refresh_all_cases(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Dispara una tarea en segundo plano para recorrer todos los casos v?lidos."""
    if REFRESH_LOCK.locked():
        return {"ok": False, "message": "Ya existe una actualizaci?n masiva en curso. Por favor, espere a que termine."}
    
    background_tasks.add_task(do_auto_refresh_with_lock)
    return {"ok": True, "message": "Sincronizaci?n masiva iniciada en segundo plano."}

async def do_auto_refresh_with_lock():
    if REFRESH_LOCK.locked():
        return
    async with REFRESH_LOCK:
        await do_auto_refresh()


# =========================
# DOCUMENTOS DE ACTUACIN
# =========================
@app.get("/cases/events/{id_reg_actuacion}/documents")
async def get_event_documents(
    id_reg_actuacion: int,
    llave_proceso: str = Query(..., description="La llave (radicado) del proceso de 23 digitos"),
    db: Session = Depends(get_db)
):
    print(f"\n [DOCS] id_reg_actuacion={id_reg_actuacion} | llave_proceso={llave_proceso}")

    # 1. Intentar obtener de la base de datos (caché) para velocidad instantánea
    try:
        event = db.query(CaseEvent).filter(CaseEvent.id_reg_actuacion == id_reg_actuacion).first()
        if event and event.documentos_cache:
            print(f" [DOCS] Retornando desde cache para id_reg_actuacion={id_reg_actuacion}")
            cached_items = json.loads(event.documentos_cache)
            return {"items": cached_items, "total": len(cached_items)}
    except Exception as e:
        print(f" [DOCS] Error leyendo cache de BD: {e}")
        db.rollback()

    items = []

    # 2. Si no hay cache, hacer la consulta externa normal
    try:
        raw = await asyncio.wait_for(documentos_actuacion(id_reg_actuacion, llave_proceso), timeout=20.0)
        print(f" [DOCS] service/rama.documentos_actuacion()  tipo={type(raw).__name__} | valor={str(raw)[:300]}")
        items = extract_documentos_from_response(raw)
        print(f" [DOCS] items extrados del servicio: {len(items)}")
    except asyncio.TimeoutError:
        print(" [DOCS] Timeout de 20s en documentos_actuacion")
    except RamaError as e:
        print(f" [DOCS] RamaError en servicio: {e}")
    except Exception as e:
        print(f" [DOCS] Error en servicio: {e}")
        traceback.print_exc()

    if not items:
        print(f" [DOCS] Servicio retorn vaco o timeout. Intentando llamada directa a Rama Judicial...")
        try:
            items = await asyncio.wait_for(fetch_documentos_rama_directa(id_reg_actuacion, llave_proceso), timeout=20.0)
            print(f" [DOCS] items desde llamada directa: {len(items)}")
        except asyncio.TimeoutError:
            print(" [DOCS] Timeout de 20s en fetch_documentos_rama_directa")
        except Exception as e:
            print(f" [DOCS] Error en llamada directa: {e}")
            traceback.print_exc()
            
    if not items:
        raise HTTPException(504, "La Rama Judicial tardó demasiado en responder o no entregó documentos. Intenta de nuevo más tarde.")

    # 3. Guardar en la base de datos si obtuvimos resultados
    try:
        event = db.query(CaseEvent).filter(CaseEvent.id_reg_actuacion == id_reg_actuacion).first()
        if event:
            event.documentos_cache = json.dumps(items)
            db.commit()
            print(f" [DOCS] Guardado en cache exitosamente ({len(items)} items).")
    except Exception as e:
        db.rollback()
        print(f" [DOCS] Error guardando cache en BD: {e}")

    print(f" [DOCS] Resultado final  {len(items)} documentos")
    return {"items": items, "total": len(items)}


# =========================
# DESCARGA DE DOCUMENTO (PROXY A RAMA JUDICIAL)
# =========================
@app.get("/documentos/{id_documento}/descargar")
async def descargar_documento_endpoint(id_documento: int):
    url_rama = f"{RAMA_BASE}/Descarga/Documento/{id_documento}"
    print(f" Descargando documento ID={id_documento}  {url_rama}")

    try:
        client = httpx.AsyncClient(timeout=60.0, verify=False, headers=RAMA_HEADERS, follow_redirects=True)
        response = await client.send(
            client.build_request("GET", url_rama),
            stream=True
        )

        print(f" Status Rama Judicial: {response.status_code}")

        if response.status_code >= 400:
            await response.aclose()
            await client.aclose()
            raise HTTPException(
                status_code=response.status_code,
                detail=f"La Rama Judicial devolvi {response.status_code} para el documento {id_documento}."
            )

        content_type = response.headers.get("content-type", "application/pdf")
        if "octet-stream" in content_type:
            content_type = "application/pdf"

        async def stream_content():
            try:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk
            finally:
                await response.aclose()
                await client.aclose()

        return StreamingResponse(
            stream_content(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="documento_rama_{id_documento}.pdf"',
                "Cache-Control": "no-cache",
            }
        )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, f"Timeout: La Rama Judicial tard demasiado (documento {id_documento}).")
    except httpx.ConnectError as e:
        raise HTTPException(502, f"No se pudo conectar a la Rama Judicial: {str(e)}")
    except Exception as e:
        print(f" Error inesperado descargando {id_documento}: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Error interno descargando documento: {str(e)}")

# =========================
# PUBLICACIONES PROCESALES
# =========================
@app.get("/cases/{radicado}/publicaciones")
async def get_case_publications(
    radicado: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q_case = db.query(Case).filter(Case.radicado == radicado)
    if not current_user.is_admin and current_user.company_id:
        q_case = q_case.filter(Case.company_id == current_user.company_id)
    
    case = q_case.first()
    
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
        
    pubs = db.query(CasePublication).filter(CasePublication.case_id == case.id).order_by(desc(CasePublication.fecha_publicacion)).all()
    
    # Auto-encolar búsquedas si faltan (liviano, sin scraping web)
    from backend.service.publicaciones import auto_queue_publicaciones
    auto_queue_publicaciones(db, radicado, force=False, source_trigger="view_case")
    
    # Consultar estado de la cola
    from backend.models import CasePublicationSearch
    busquedas_db = db.query(CasePublicationSearch).filter(CasePublicationSearch.radicado == radicado).all()
    
    # Estado consolidado para compatibilidad
    global_status = "completado"
    if any(b.estado in ["pendiente", "procesando"] for b in busquedas_db):
        global_status = "procesando"
    elif not pubs and any(b.estado == "error" for b in busquedas_db):
        global_status = "error"
    elif not pubs and any(b.estado == "sin_resultado" for b in busquedas_db):
        global_status = "sin_resultado"
        
    return {
        "radicado": radicado,
        "items": [
            {
                "id": p.id,
                "fecha_publicacion": p.fecha_publicacion.isoformat() if p.fecha_publicacion else None,
                "tipo_publicacion": p.tipo_publicacion,
                "descripcion": p.descripcion,
                "documento_url": p.documento_url,
                "source_url": p.source_url,
                "source_id": p.source_id,
                "fecha_estado_electronico": p.fecha_estado_electronico.isoformat() if p.fecha_estado_electronico else None,
                "numero_estado": p.numero_estado,
                "match_fuerte": p.match_fuerte,
                "match_type": p.match_type,
                "motivo_match": p.motivo_match,
                "url_fuente_principal": p.url_fuente_principal,
                "tipo_fuente_principal": p.tipo_fuente_principal,
                "documentos_complementarios": p.documentos_complementarios,
                "url_resumen_publicacion": p.url_resumen_publicacion,
                "url_cuadro": p.url_cuadro,
                "url_providencia": p.url_providencia,
                "observacion": p.observacion,
                # Campos de validación estricta
                "estado_validacion": getattr(p, "estado_validacion", "requiere_revision") or "requiere_revision",
                "match_score": getattr(p, "match_score", 0),
                "texto_bloque_match": getattr(p, "texto_bloque_match", ""),
                "motivo_descarte": getattr(p, "motivo_descarte", ""),
                "fuente_principal_validada": getattr(p, "fuente_principal_validada", False),
                "requiere_revision": getattr(p, "requiere_revision", True),
                "elementos_detectados": getattr(p, "elementos_detectados", ""),
                "documento_nombre": getattr(p, "documento_nombre", ""),
                "extraction_quality": getattr(p, "extraction_quality", "")
            }
            for p in pubs if getattr(p, "estado_validacion", "requiere_revision") != "descartado"
        ],
        "busquedas": [
            {
                "mes_busqueda": b.mes_busqueda,
                "estado": b.estado,
                "fecha_ultima_busqueda": b.fecha_ultima_busqueda.isoformat() if b.fecha_ultima_busqueda else None,
                "error": b.ultimo_error or b.error,
                "intentos": getattr(b, "intentos", 0)
            }
            for b in busquedas_db
        ],
        "estado_busqueda": global_status,
        "sync_pub_status": global_status,
        "sync_pub_progress": 100 if global_status != "procesando" else 50
    }

@app.get("/api/cases/id/{case_id}/publicaciones")
@app.get("/cases/id/{case_id}/publicaciones")
async def get_case_publications_by_id(
    case_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q_case = db.query(Case).filter(Case.id == case_id)
    if not current_user.is_admin and current_user.company_id:
        q_case = q_case.filter(Case.company_id == current_user.company_id)
        
    case = q_case.first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    return await get_case_publications(case.radicado, db, current_user)

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.models import AuditLog, User

class DescartarRequest(BaseModel):
    motivo: str
    observacion: Optional[str] = None

class AprobarRequest(BaseModel):
    observacion: Optional[str] = None

@app.post("/api/publicaciones/{pub_id}/descartar")
@app.post("/publicaciones/{pub_id}/descartar")
async def descartar_publicacion(
    pub_id: int, 
    req: DescartarRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pub = db.query(CasePublication).filter(CasePublication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
        
    pub.estado_validacion = "descartado"
    pub.motivo_descarte = req.motivo
    pub.requiere_revision = False
    
    pub.descartado_manual = True
    pub.descartado_por_id = current_user.id
    pub.discarded_at = datetime.now()
    if req.observacion:
        pub.observacion_revision = req.observacion
    
    audit = AuditLog(
        user_id=current_user.id,
        accion="DISCARD_PUBLICATION",
        entidad="CasePublication",
        entidad_id=pub.id,
        metadata_json=f'{{"motivo": "{req.motivo}", "observacion": "{req.observacion or ""}"}}'
    )
    db.add(audit)
    db.commit()
    
    return {"ok": True, "message": "Publicación descartada correctamente", "id": pub_id}

@app.post("/api/publicaciones/{pub_id}/aprobar")
@app.post("/publicaciones/{pub_id}/aprobar")
async def aprobar_publicacion(
    pub_id: int, 
    req: AprobarRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pub = db.query(CasePublication).filter(CasePublication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
        
    pub.estado_validacion = "validado"
    pub.requiere_revision = False
    
    pub.match_score = 100
    pub.match_type = "validacion_manual"
    pub.validado_manual = True
    pub.aprobado_por_id = current_user.id
    pub.approved_at = datetime.now()
    
    if req.observacion:
        pub.observacion_revision = req.observacion
        pub.motivo_match = (pub.motivo_match or "") + f" [Validación Manual: {req.observacion}]"
    else:
        pub.motivo_match = (pub.motivo_match or "") + " [Validación Manual]"
    
    audit = AuditLog(
        user_id=current_user.id,
        accion="APPROVE_PUBLICATION",
        entidad="CasePublication",
        entidad_id=pub.id,
        metadata_json=f'{{"observacion": "{req.observacion or ""}"}}'
    )
    db.add(audit)
    db.commit()
    
    return {"ok": True, "message": "Publicación validada manualmente", "id": pub_id}
@app.post("/api/cases/{radicado}/sync-publications")
@app.post("/cases/{radicado}/sync-publications")
async def sync_case_publications(radicado: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.radicado == radicado).first()
    if not case: return {"ok": False, "error": "Caso no encontrado"}
    
    # RESET INMEDIATO
    case.sync_pub_progress = 5
    case.sync_pub_status = "Iniciando búsqueda..."
    db.commit()
    
    background_tasks.add_task(run_sync_publications_task, case.radicado, True)
    return {"ok": True, "message": "Sincronización iniciada en segundo plano"}

@app.post("/api/cases/id/{case_id}/refresh-publicaciones")
@app.post("/cases/id/{case_id}/refresh-publicaciones")
async def refresh_publications_by_id(case_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case: return {"ok": False, "error": "Caso no encontrado"}
    
    from backend.service.publicaciones import auto_queue_publicaciones
    queued = auto_queue_publicaciones(db, case.radicado, force=True, source_trigger="manual_refresh")
    
    if queued > 0:
        return {"ok": True, "message": f"Sincronización forzada iniciada para {queued} mes(es)."}
    else:
        return {"ok": True, "message": "El caso no tiene actuaciones relevantes para buscar publicaciones."}

@app.post("/api/cases/{radicado}/reset-sync")
@app.post("/cases/{radicado}/reset-sync")
async def reset_case_sync(radicado: str, db: Session = Depends(get_db)):
    """Resetea manualmente el estado de sincronización si se queda trabado."""
    case = db.query(Case).filter(Case.radicado == radicado).first()
    if not case: return {"ok": False, "error": "Caso no encontrado"}
    case.sync_pub_status = None
    case.sync_pub_progress = 0
    db.commit()
    return {"ok": True, "message": "Estado de sincronización reseteado."}

# Estado global del proceso de sincronización masiva (en memoria, suficiente para un proceso)
_bulk_sync_state = {
    "running": False,
    "total": 0,
    "reviewed": 0,
    "errors": 0,
}

@app.get("/api/bulk-sync/publications-status")
@app.get("/bulk-sync/publications-status")
async def get_sync_publications_status():
    """Devuelve el progreso actual de la sincronización masiva."""
    return {
        "running": _bulk_sync_state["running"],
        "total": _bulk_sync_state["total"],
        "reviewed": _bulk_sync_state["reviewed"],
        "errors": _bulk_sync_state["errors"],
        "percent": round((_bulk_sync_state["reviewed"] / _bulk_sync_state["total"]) * 100)
                   if _bulk_sync_state["total"] > 0 else 0,
    }

@app.post("/api/cases/sync-all-publications")
@app.post("/cases/sync-all-publications")
async def sync_all_publications(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Inicia la sincronización masiva de publicaciones procesales para todos los casos válidos.
    El proceso se ejecuta en segundo plano con baja concurrencia para no saturar el portal.
    """
    # Casos válidos = los que ya tienen juzgado asignado (fueron encontrados en Rama Judicial)
    cases = db.query(Case).filter(Case.juzgado.isnot(None)).all()
    total = len(cases)
    if total == 0:
        return {"ok": True, "message": "No hay casos válidos para sincronizar.", "total": 0}

    if _bulk_sync_state["running"]:
        return {
            "ok": False,
            "message": f"Ya hay una sincronización en curso ({_bulk_sync_state['reviewed']}/{_bulk_sync_state['total']} revisados).",
            "total": _bulk_sync_state["total"],
            "reviewed": _bulk_sync_state["reviewed"],
        }

    async def run_bulk_sync():
        _bulk_sync_state["running"] = True
        _bulk_sync_state["total"] = total
        _bulk_sync_state["reviewed"] = 0
        _bulk_sync_state["errors"] = 0
        db_bulk = SessionLocal()
        try:
            radicados = [c.radicado for c in db_bulk.query(Case).filter(Case.juzgado.isnot(None)).all()]
            for radicado in radicados:
                try:
                    await run_sync_publications_task(radicado, force=False)
                except Exception as e:
                    _bulk_sync_state["errors"] += 1
                    print(f"[bulk_sync] Error en {radicado}: {e}")
                finally:
                    _bulk_sync_state["reviewed"] += 1
        finally:
            db_bulk.close()
            _bulk_sync_state["running"] = False

    background_tasks.add_task(run_bulk_sync)
    return {
        "ok": True,
        "message": f"Sincronización masiva iniciada para {total} casos en segundo plano.",
        "total": total
    }

@app.get("/api/sync/logs/{case_id}")
async def get_sync_logs(case_id: int, db: Session = Depends(get_db)):
    """Permite ver los logs de diagnóstico desde el navegador."""
    logs = db.execute(text("SELECT message, created_at FROM sync_debug_logs WHERE case_id = :cid ORDER BY created_at DESC LIMIT 100"), 
                     {"cid": case_id}).fetchall()
    return [{"message": r[0], "at": r[1].isoformat()} for r in logs]

class BuscarMesBody(BaseModel):
    radicado: str
    mes: str # Formato YYYY-MM
    prioridad: int = 1
    
@app.post("/api/publicaciones/buscar-mes")
@app.post("/publicaciones/buscar-mes")
async def force_search_month(body: BuscarMesBody, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.radicado == body.radicado).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
        
    from backend.models import CasePublicationSearch
    
    # Buscar si ya existe la búsqueda para ese mes
    busqueda = db.query(CasePublicationSearch).filter(
        CasePublicationSearch.radicado == body.radicado,
        CasePublicationSearch.mes_busqueda == body.mes
    ).first()
    
    if busqueda:
        busqueda.estado = "pendiente"
        busqueda.intentos = 0
        busqueda.error = None
        busqueda.ultimo_error = None
        busqueda.prioridad = body.prioridad
        busqueda.locked_at = None
        busqueda.locked_by = None
        busqueda.source_trigger = "manual_override"
        busqueda.force = True
    else:
        busqueda = CasePublicationSearch(
            radicado=body.radicado,
            estado="pendiente",
            mes_busqueda=body.mes,
            intentos=0,
            prioridad=body.prioridad,
            source_trigger="manual_override",
            force=True
        )
        db.add(busqueda)
        
    db.commit()
    
    return {"ok": True, "message": f"Búsqueda del mes {body.mes} encolada exitosamente para el radicado {body.radicado}.", "estado": "pendiente"}

class PublicacionesDebugBody(BaseModel):
    radicado: str
    force: Optional[bool] = False

@app.post("/publicaciones/buscar/{radicado}")
async def force_sync_publications_by_radicado(radicado: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.radicado == radicado).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    case.sync_pub_progress = 5
    case.sync_pub_status = "Iniciando búsqueda forzada..."
    db.commit()
    
    async def run_force_sync():
        async with sync_pub_semaphore:
            db_session = SessionLocal()
            try:
                c = db_session.query(Case).filter(Case.id == case.id).first()
                if c:
                    await save_new_publications(c, db_session, force=True)
            except Exception as e:
                print(f"[force_sync] Error: {e}")
            finally:
                db_session.close()

    background_tasks.add_task(run_force_sync)
    return {"ok": True, "message": "Búsqueda forzada iniciada en segundo plano."}

@app.post("/api/publicaciones/debug")
@app.post("/publicaciones/debug")
async def debug_publications_search(body: PublicacionesDebugBody, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.radicado == body.radicado).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado en la base de datos.")

    from backend.service.publicaciones import (
        is_relevant_actuacion, get_search_months_for_actuacion,
        build_portal_search_url, parse_fecha_pub,
        parse_result_cards, filter_cards_by_despacho, filter_cards_by_category,
        detect_main_sources, extract_text_content, validate_strong_match,
        revisar_documentos_complementarios, guardar_publicacion_validada,
        parse_spanish_date, extract_metadata_field, HEADERS
    )
    import calendar
    import hashlib
    from datetime import date, datetime
    import httpx
    from bs4 import BeautifulSoup
    import re

    # 1. Obtener actuaciones del caso
    eventos = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.event_date.asc()).all()
    
    actuaciones_relevantes = []
    seen_dates = set()
    for ev in eventos:
        act_text = getattr(ev, "title", "") or getattr(ev, "actuacion", "") or ""
        if is_relevant_actuacion(act_text):
            raw_date = getattr(ev, "event_date", "") or getattr(ev, "fecha_actuacion", "")
            if raw_date:
                if isinstance(raw_date, (date, datetime)):
                    dt = raw_date
                else:
                    try:
                        dt = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d")
                    except:
                        continue
                if isinstance(dt, datetime):
                    dt = dt.date()
                
                if dt not in seen_dates:
                    seen_dates.add(dt)
                    actuaciones_relevantes.append({
                        "fecha": dt.strftime("%Y-%m-%d"),
                        "descripcion": act_text
                    })

    # 2. Calcular meses a buscar
    meses_a_buscar_tuples = set()
    for dt in seen_dates:
        for mes in get_search_months_for_actuacion(dt):
            meses_a_buscar_tuples.add(mes)
            
    meses_a_buscar = [f"{y}-{m:02d}" for y, m in sorted(meses_a_buscar_tuples)]

    resultados_por_mes = {}
    
    # 3. Buscar para cada mes si force es True, o si no se ha buscado
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        for year, month in sorted(meses_a_buscar_tuples):
            month_str = f"{year}-{month:02d}"
            fecha_inicio_str = f"{year}-{month:02d}-01"
            last_day = calendar.monthrange(year, month)[1]
            fecha_fin_str = f"{year}-{month:02d}-{last_day:02d}"
            
            search_url = build_portal_search_url(case.radicado[:12], fecha_inicio_str, fecha_fin_str)
            
            month_res = {
                "buscado": True,
                "url": search_url,
                "cards_count": 0,
                "detalles_abiertos": 0,
                "fuentes_revisadas": 0,
                "matches": [],
                "guardadas": [],
                "motivo_no_resultado": ""
            }
            
            try:
                resp = await client.get(search_url)
                if resp.status_code != 200:
                    month_res["motivo_no_resultado"] = f"Error portal HTTP {resp.status_code}"
                    resultados_por_mes[month_str] = month_res
                    continue
                    
                raw_cards = parse_result_cards(resp.text)
                month_res["cards_count"] = len(raw_cards)
                
                filtered_by_despacho = filter_cards_by_despacho(raw_cards, case.radicado[:12])
                candidates = filter_cards_by_category(filtered_by_despacho)
                
                if not candidates:
                    month_res["motivo_no_resultado"] = "No se encontraron candidatos despues de filtrar por despacho y categoria."
                    resultados_por_mes[month_str] = month_res
                    continue
                    
                for cand in candidates:
                    month_res["detalles_abiertos"] += 1
                    detail_resp = await client.get(cand["detail_url"])
                    if detail_resp.status_code != 200:
                        continue
                        
                    detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                    estado_no = extract_metadata_field(detail_soup, "Estado No.")
                    if not estado_no:
                        title_match = re.search(r'Estado No\.?\s*(\d+)', cand["title"], re.IGNORECASE)
                        if title_match:
                            estado_no = title_match.group(1)
                            
                    fecha_estado_electronico_str = extract_metadata_field(detail_soup, "Fecha de Estado Electrónico")
                    fecha_estado_electronico = None
                    if fecha_estado_electronico_str:
                        fecha_estado_electronico = parse_spanish_date(fecha_estado_electronico_str)
                    if not fecha_estado_electronico:
                        fecha_estado_electronico = parse_fecha_pub(cand["fecha_publicacion"])
                        
                    fuentes = detect_main_sources(detail_resp.text)
                    
                    matched_any = False
                    for source in fuentes:
                        month_res["fuentes_revisadas"] += 1
                        doc_text = await extract_text_content(source["url"], client)
                        match = validate_strong_match(doc_text, case.radicado, case.demandante or "", case.demandado or "")
                        
                        if match.is_valid:
                            matched_any = True
                            month_res["matches"].append({
                                "title": cand["title"],
                                "match_type": match.match_type,
                                "reasons": match.reasons
                            })
                            
                            # Guardar la publicación validada
                            p_data = {
                                "radicado": case.radicado,
                                "case_id": case.id,
                                "fecha_publicacion": cand["fecha_publicacion"],
                                "tipo": cand["categoria"],
                                "descripcion": cand["title"],
                                "documento_url": source["url"],
                                "source_url": cand["detail_url"],
                                "source_id": hashlib.md5(cand["detail_url"].encode()).hexdigest(),
                                "url_fuente_principal": source["url"],
                                "tipo_fuente_principal": source["tipo"],
                                "texto_fuente_principal": doc_text,
                                "validada_por_fuente_principal": True,
                                "numero_estado": estado_no or "",
                                "fecha_estado_electronico": fecha_estado_electronico.strftime("%Y-%m-%d") if fecha_estado_electronico else cand["fecha_publicacion"],
                                "match_fuerte": True,
                                "match_type": match.match_type,
                                "motivo_match": match.reasons,
                                "observacion": f"Debug sync. Validada por {source['tipo']}."
                            }
                            saved = guardar_publicacion_validada(db, p_data)
                            if saved:
                                month_res["guardadas"].append({
                                    "title": cand["title"],
                                    "fecha": cand["fecha_publicacion"]
                                })
                            break
                            
                if not month_res["matches"]:
                    month_res["motivo_no_resultado"] = "No se encontro ninguna coincidencia fuerte en los documentos de los candidatos."
                    
            except Exception as ex:
                month_res["motivo_no_resultado"] = f"Excepcion en busqueda: {str(ex)}"
                
            resultados_por_mes[month_str] = month_res

    return {
        "radicado": case.radicado,
        "actuaciones_relevantes": actuaciones_relevantes,
        "meses_a_buscar": meses_a_buscar,
        "resultados_por_mes": resultados_por_mes
    }

# Semáforo global para evitar saturación y bloqueos de DB (Máximo 2 sincronizaciones pesadas a la vez)
sync_pub_semaphore = asyncio.Semaphore(2)

async def run_sync_publications_task(radicado: str, force: bool = False):
    """Wrapper para encolar la sincronización en background."""
    db = SessionLocal()
    try:
        from backend.service.publicaciones import auto_queue_publicaciones
        auto_queue_publicaciones(db, radicado, force=force, source_trigger="manual_sync")
    except Exception as e:
        print(f"[sync_task] Error: {e}")
    finally:
        db.close()

async def save_new_publications_task(case_id: int):
    """Wrapper task to enqueue sync logic in the background."""
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            from backend.service.publicaciones import auto_queue_publicaciones
            auto_queue_publicaciones(db, case.radicado, force=False, source_trigger="auto_sync_case")
    except Exception as e:
        print(f"[save_new_publications_task] Error: {e}")
    finally:
        db.close()

def update_sync_progress(db: Session, case_id: int, progress: int, status: str = None):
    """Actualiza el progreso y guarda un log en la DB para diagnóstico."""
    try:
        # 1. Actualizar caso
        params = {"prog": progress, "cid": case_id}
        sql = "UPDATE cases SET sync_pub_progress = :prog"
        if status is not None:
            sql += ", sync_pub_status = :stat"
            params["stat"] = status
        sql += " WHERE id = :cid"
        db.execute(text(sql), params)
        
        # 2. Guardar log de debug
        log_msg = f"Progreso: {progress}% | Status: {status or 'N/A'}"
        db.execute(text("INSERT INTO sync_debug_logs (case_id, message) VALUES (:cid, :msg)"), 
                   {"cid": case_id, "msg": log_msg})
        
        db.commit()
    except Exception as e:
        print(f"[progress-error] {e}")
        db.rollback()

async def save_new_publications(case: Case, db: Session, force: bool = False):
    try:
        from backend.service.publicaciones import (
            is_relevant_actuacion, get_search_months_for_actuacion,
            consultar_publicaciones_rango, parse_fecha_pub,
            guardar_estado_busqueda, guardar_publicacion_validada
        )
        from backend.models import CaseEvent, CasePublication, CasePublicationSearch
        import asyncio
        import calendar
        from datetime import datetime, timedelta, date

        # 0. Iniciar progreso
        with open("sync_emergency.log", "a") as f:
            f.write(f"[{datetime.now()}] Iniciando tarea para {case.radicado} (ID: {case.id}) | Force: {force}\n")
                
        update_sync_progress(db, case.id, 5, "Iniciando búsqueda...")
        
        with open("sync_debug.log", "a") as f_log:
            f_log.write(f"\n[{datetime.now()}] SYNC START: {case.radicado} | Force: {force}")

        update_sync_progress(db, case.id, 10, "Analizando historial de actuaciones...")
        
        # 1. Obtener actuaciones del caso
        eventos = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.event_date.desc()).all()
        
        # Filtrar y agrupar actuaciones relevantes por fecha exacta
        actuaciones_relevantes = []
        seen_dates = set()
        for ev in eventos:
            act_text = getattr(ev, "title", "") or getattr(ev, "actuacion", "") or ""
            if is_relevant_actuacion(act_text):
                raw_date = getattr(ev, "event_date", "") or getattr(ev, "fecha_actuacion", "")
                if raw_date:
                    if isinstance(raw_date, (date, datetime)):
                        dt = raw_date
                    else:
                        try:
                            dt = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d")
                        except:
                            continue
                    
                    if isinstance(dt, datetime):
                        dt = dt.date()
                    if dt not in seen_dates:
                        seen_dates.add(dt)
                        actuaciones_relevantes.append(dt)

        if not actuaciones_relevantes:
            if not force:
                # Marcar no requiere búsqueda
                guardar_estado_busqueda(db, {
                    "radicado": case.radicado,
                    "fecha_actuacion": date.today(),
                    "estado_busqueda": "no_requiere_busqueda",
                    "debug": "No se encontraron actuaciones relevantes para este radicado."
                })
                update_sync_progress(db, case.id, 100, "No se detectaron actuaciones relevantes.")
                return
            else:
                # Búsqueda manual forzada: buscar en el mes actual y el anterior (por si apenas lo publicaron)
                print(f"[sync] Busqueda forzada sin actuaciones relevantes para {case.radicado}. Usando mes actual y anterior.")
                hoy = date.today()
                actuaciones_relevantes = [hoy]
                
                # Agregar el mes pasado para mayor cobertura en búsquedas forzadas
                primer_dia = hoy.replace(day=1)
                mes_pasado = primer_dia - timedelta(days=1)
                actuaciones_relevantes.append(mes_pasado)
                seen_dates = {hoy, mes_pasado}

        # Calcular todos los meses a buscar (evitando duplicados)
        meses_a_buscar = set()
        for dt in actuaciones_relevantes:
            for mes in get_search_months_for_actuacion(dt):
                meses_a_buscar.add(mes)

        found_pubs = []
        total_months = len(meses_a_buscar)
        
        for i, (year, month) in enumerate(sorted(meses_a_buscar)):
            prog = 10 + int((i / total_months) * 85)
            month_name = MONTHS_ES[month-1] if 1 <= month <= 12 else str(month)
            update_sync_progress(db, case.id, prog, f"Buscando para {month_name} de {year}...")
            
            fecha_inicio = date(year, month, 1)
            fecha_fin = date(year, month, calendar.monthrange(year, month)[1])
            
            # Buscar si ya existe publicación válida para este mes (si no es forzado)
            if not force:
                ya_existe_valida = db.query(CasePublication).filter(
                    CasePublication.case_id == case.id,
                    CasePublication.match_fuerte == True,
                    (
                        ((CasePublication.fecha_publicacion >= fecha_inicio) & (CasePublication.fecha_publicacion <= fecha_fin)) |
                        ((CasePublication.fecha_estado_electronico >= fecha_inicio) & (CasePublication.fecha_estado_electronico <= fecha_fin))
                    )
                ).count() > 0
                if ya_existe_valida:
                    print(f"[sync] Saltando busqueda para {case.radicado} en {year}-{month:02d} (ya existe publicacion valida)")
                    continue

                # Comprobar log de búsquedas recientes (<24 horas)
                search_record = db.query(CasePublicationSearch).filter(
                    CasePublicationSearch.radicado == case.radicado,
                    CasePublicationSearch.fecha_inicio_busqueda == fecha_inicio
                ).first()
                
                should_search = True
                if search_record:
                    if search_record.estado_busqueda == "buscando":
                        print(f"[sync] Saltando busqueda para {case.radicado} en {year}-{month:02d} (ya hay una busqueda activa)")
                        should_search = False
                    elif search_record.estado_busqueda in ["sin_resultado", "error", "no_requiere_busqueda"] and search_record.fecha_ultima_busqueda:
                        if datetime.now() - search_record.fecha_ultima_busqueda < timedelta(hours=24):
                            print(f"[sync] Saltando busqueda reciente (<24h) para {case.radicado} en {year}-{month:02d} (estado: {search_record.estado_busqueda})")
                            should_search = False
                
                if not should_search:
                    continue

            # Determinar fecha de actuación desencadenante para este mes
            fecha_actuacion_del_mes = None
            for dt in sorted(seen_dates):
                if dt.year == year and dt.month == month:
                    fecha_actuacion_del_mes = dt
                    break
            if not fecha_actuacion_del_mes:
                # Comprobar si fue desencadenada por el mes anterior (fin de mes)
                if month == 1:
                    prev_year, prev_month = year - 1, 12
                else:
                    prev_year, prev_month = year, month - 1
                for dt in sorted(seen_dates):
                    if dt.year == prev_year and dt.month == prev_month and dt.day >= 25:
                        fecha_actuacion_del_mes = dt
                        break
            if not fecha_actuacion_del_mes:
                fecha_actuacion_del_mes = list(seen_dates)[0]
                
            # Registrar inicio de búsqueda en DB
            guardar_estado_busqueda(db, {
                "radicado": case.radicado,
                "fecha_actuacion": fecha_actuacion_del_mes,
                "fecha_inicio_busqueda": fecha_inicio,
                "fecha_fin_busqueda": fecha_fin,
                "despacho_codigo": case.radicado[:12],
                "estado_busqueda": "buscando",
                "intento_manual": force
            })
            db.commit()
            
            try:
                # Ejecutar búsqueda para el mes
                results = await consultar_publicaciones_rango(
                    radicado_completo=case.radicado,
                    fecha_act_str=fecha_actuacion_del_mes.strftime("%Y-%m-%d"),
                    demandante=case.demandante or "",
                    demandado=case.demandado or "",
                    year=year,
                    month=month
                )
                
                estado_fin = "encontrada" if results else "sin_resultado"
                guardar_estado_busqueda(db, {
                    "radicado": case.radicado,
                    "fecha_actuacion": fecha_actuacion_del_mes,
                    "fecha_inicio_busqueda": fecha_inicio,
                    "fecha_fin_busqueda": fecha_fin,
                    "despacho_codigo": case.radicado[:12],
                    "estado_busqueda": estado_fin,
                    "intento_manual": force
                })
                db.commit()
                
                if results:
                    found_pubs.extend(results)
            except Exception as e:
                print(f"[sync] Error en búsqueda de {year}-{month:02d}: {e}")
                guardar_estado_busqueda(db, {
                    "radicado": case.radicado,
                    "fecha_actuacion": fecha_actuacion_del_mes,
                    "fecha_inicio_busqueda": fecha_inicio,
                    "fecha_fin_busqueda": fecha_fin,
                    "despacho_codigo": case.radicado[:12],
                    "estado_busqueda": "error",
                    "error": str(e),
                    "intento_manual": force
                })
                db.commit()

        # 3. Guardar resultados
        update_sync_progress(db, case.id, 96, "Guardando publicaciones encontradas...")
        saved_count = 0
        seen_ids = set()
        for p in found_pubs:
            sid = p.get("source_id")
            if not sid or sid in seen_ids:
                continue
            seen_ids.add(sid)
            
            p["case_id"] = case.id
            p["radicado"] = case.radicado
            if "fecha_publicacion" not in p and "fecha" in p:
                p["fecha_publicacion"] = p["fecha"]
                
            guardar_publicacion_validada(db, p)
            saved_count += 1
            
        update_sync_progress(db, case.id, 100, f"Completado: {saved_count} publicaciones procesadas.")
        
        await asyncio.sleep(5)
        update_sync_progress(db, case.id, 0, "")

    except Exception as e:
        import traceback
        print(f"[save_new_pubs] Error general: {e}")
        traceback.print_exc()
        update_sync_progress(db, case.id, 0, f"Error: {str(e)[:40]}")
        try:
            case.sync_pub_status = f"Error: {str(e)[:50]}"
            case.sync_pub_progress = 0
            db.commit()
        except: pass

@app.post("/admin/backfill-publicaciones")
async def backfill_publicaciones(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Escanea todos los casos existentes y busca publicaciones para actuaciones relevantes (en segundo plano)."""
    background_tasks.add_task(run_backfill_publicaciones_task)
    return {"status": "ok", "message": "Puesta al da masiva de publicaciones iniciada en segundo plano."}

async def run_backfill_publicaciones_task():
    """Ejecuta el backfill de publicaciones de forma segura en segundo plano."""
    db = SessionLocal()
    try:
        cases = db.query(Case).all()
        count = 0
        print(f"[backfill] Iniciando puesta al da masiva para {len(cases)} casos...")
        for case in cases:
            # save_new_publications ya maneja el filtro estricto de keywords
            await save_new_publications(case, db)
            count += 1
            if count % 10 == 0:
                print(f"[backfill] Procesados {count}/{len(cases)} casos...")
                db.commit()
        db.commit()
        print(f"[backfill] Finalizado. Procesados {count} casos.")
    except Exception as e:
        print(f"[backfill] Error en proceso masivo: {e}")
    finally:
        db.close()

# =========================
# BSQUEDA MASIVA (NAMES / RADICADOS)
# =========================

@app.post("/search/names/upload")
async def upload_names_search(
    background_tasks: BackgroundTasks,
    from_date: str | None = None,
    to_date: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Crear el Job
    job = SearchJob(job_type="name", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    # 2. Leer contenido y lanzar tarea en segundo plano
    content = await file.read()
    
    date_range = {"from": from_date, "to": to_date}
    
    # Pasamos una factora de sesin para que el hilo de fondo tenga su propia DB connection
    background_tasks.add_task(run_name_search_job, job.id, content, lambda: SessionLocal(), date_range)

    return {"job_id": job.id, "status": "pending"}

@app.post("/search/radicados/upload")
async def upload_radicados_search(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Crear el Job
    job = SearchJob(job_type="radicado", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    # 2. Leer contenido y lanzar tarea en segundo plano
    content = await file.read()
    
    from backend.service.bulk_orchestrator import run_radicado_search_job
    background_tasks.add_task(run_radicado_search_job, job.id, content, lambda: SessionLocal())

    return {"job_id": job.id, "status": "pending"}

@app.get("/search/jobs/{job_id}")
async def get_search_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    results = []
    if job.results_json:
        results = json.loads(job.results_json)

    return {
        "id": job.id,
        "type": job.job_type,
        "status": job.status,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "results": results,
        "error": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }

@app.post("/search/jobs/{job_id}/import")
async def import_search_results(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        body = await request.json()
        selected_indices = body.get("indices", [])
        
        job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
        if not job or not job.results_json:
            raise HTTPException(status_code=404, detail="Resultados no encontrados")
        
        all_results = json.loads(job.results_json)
        # Filtrar los seleccionados por el usuario
        selected_data = [res for res in all_results if res.get("index") in selected_indices]
        
        imported_count = 0
        for item in selected_data:
            sel = item.get("selected")
            if not sel: continue
            
            # Verificar si ya existe por idProceso (prioridad) o radicado
            id_proceso = str(sel.get("idProceso")) if sel.get("idProceso") else None
            radicado = str(sel.get("llaveProceso") or sel.get("numero", ""))
            
            case = None
            if id_proceso:
                case = db.query(Case).filter(Case.id_proceso == id_proceso).first()
            if not case:
                case = db.query(Case).filter(Case.radicado == radicado).first()
            
            if not case:
                case = Case(radicado=radicado, id_proceso=id_proceso)
                db.add(case)
            
            # Actualizar datos bsicos
            # Parsear sujetos para obtener demandante/demandado si estn vacos
            sujetos_str = sel.get("sujetosProcesales") or ""
            d1, d2, _ = parse_sujetos_procesales(sujetos_str)
            
            case.demandante = d1 or sel.get("demandante") or case.demandante
            case.demandado = d2 or sel.get("demandado") or case.demandado
            case.juzgado = sel.get("despacho") or case.juzgado
            
            # Cdula y Abogado del Excel de bsqueda
            case.cedula = item.get("cedula") or case.cedula
            case.abogado = item.get("abogado") or case.abogado
            
            # Fechas
            if sel.get("fechaRadicacion"):
                try:
                    case.fecha_radicacion = parse_fecha_pub(sel["fechaRadicacion"])
                except: pass
            if sel.get("fechaUltimaActuacion"):
                try:
                    case.ultima_actuacion = parse_fecha_pub(sel["fechaUltimaActuacion"])
                except: pass
                
            imported_count += 1
        
        job.is_imported = True
        db.commit()
        return {"ok": True, "imported": imported_count}
    except Exception as e:
        db.rollback()
        log_job(f" Error en import_search_results: {str(e)}")
        log_job(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al importar: {str(e)}")

@app.get("/search/jobs/{job_id}/export")
async def export_search_results(
    job_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job or not job.results_json:
        raise HTTPException(status_code=404, detail="Resultados no encontrados")
    
    results = json.loads(job.results_json)
    
    flattened = []
    for res in results:
        base = {
            "BUSCADO": res.get("input_name1", ""),
            "CEDULA": res.get("cedula", ""),
            "ABOGADO": res.get("abogado", ""),
            "CANT_ENCONTRADOS": res.get("found_count", 0),
        }
        
        sel = res.get("selected")
        if sel:
            # Parsear sujetos para d1/d2
            sujetos_str = sel.get("sujetosProcesales") or ""
            d1, d2, _ = parse_sujetos_procesales(sujetos_str)
            
            id_p = sel.get("idProceso")
            portal_url = ""
            if id_p:
                portal_url = f"https://consultaprocesos.ramajudicial.gov.co/Consulta/Detalle?idProceso={id_p}&esPrivado=false"

            rad_val = sel.get("llaveProceso") or sel.get("numero")
            base.update({
                "RADICADO": str(rad_val) if rad_val else "No encontrado",
                "DEMANDANTE": d1 or sel.get("demandante", ""),
                "DEMANDADO": d2 or sel.get("demandado", ""),
                "DESPACHO": sel.get("despacho", ""),
                "FECHA_RADICACION": (sel.get("fechaRadicacion") or "")[:10],
                "ULTIMA_ACTUACION": (sel.get("fechaUltimaActuacion") or "")[:10],
                "ID_PROCESO": str(id_p) if id_p else "",
                "PORTAL_RAMA": portal_url
            })
        else:
            base.update({
                "RADICADO": "No encontrado",
                "DEMANDANTE": "",
                "DEMANDADO": "",
                "DESPACHO": "",
                "FECHA_RADICACION": "",
                "ULTIMA_ACTUACION": "",
                "ID_PROCESO": "",
            })
        flattened.append(base)
        
    df = pd.DataFrame(flattened)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
        workbook = writer.book
        worksheet = writer.sheets['Resultados']
        
        # Formato de texto para columnas de nmeros largos
        text_format = workbook.add_format({'num_format': '@'})
        
        # Aplicamos formato de texto a la columna RADICADO (ndice 3 usualmente: Nombre, Cdula, Abogado, Cant, RADICADO...)
        # Buscamos el ndice dinmicamente
        if "RADICADO" in df.columns:
            col_idx = df.columns.get_loc("RADICADO")
            # Aplicar a toda la columna (filas 1 a N)
            worksheet.set_column(col_idx, col_idx, 30, text_format)
            
        # Opcionalmente ajustar anchos
        worksheet.set_column('A:A', 30) # Nombre
        worksheet.set_column('H:H', 20) # Ultima Actuacin
        worksheet.set_column('I:I', 15) # ID Proceso
        worksheet.set_column('J:J', 50) # Link Portal
    
    output.seek(0)
    
    filename = f"resultado_busqueda_{job_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(output, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/cases/bulk-update-metadata")
async def bulk_update_metadata(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content))
        # Normalizar columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        updated_cases = 0
        for _, row in df.iterrows():
            radicado = str(row.get("RADICADO", "")).strip()
            if not radicado:
                continue
            
            cedula = str(row.get("CEDULA", "")).strip() if "CEDULA" in df.columns else None
            abogado = str(row.get("ABOGADO", "")).strip() if "ABOGADO" in df.columns else None
            
            # Buscamos todos los casos con este radicado
            cases = db.query(Case).filter(Case.radicado == radicado).all()
            for c in cases:
                if cedula and cedula.lower() != "nan":
                    c.cedula = cedula
                if abogado and abogado.lower() != "nan":
                    c.abogado = abogado
                updated_cases += 1
                
        db.commit()
        return {"ok": True, "updated_count": updated_cases}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando Excel: {str(e)}")


# =========================
# CLICKUP INTEGRATION
# =========================

class ClickUpImportRequest(BaseModel):
    token: str

@app.post("/projects/import-clickup")
async def import_clickup(
    data: ClickUpImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Lanza la migraci?n desde ClickUp en segundo plano."""
    from backend.clickup_sync import migrate_clickup_to_emdecob
    
    # Check admin (permitir excepcion para cuentas juridicas)
    if not current_user.is_admin and 'juri' not in current_user.username.lower() and current_user.id != 2:
        raise HTTPException(status_code=403, detail="No autorizado para realizar importacion masiva")

    async def _do_import():
        db = SessionLocal()
        try:
            await migrate_clickup_to_emdecob(data.token, db, current_user.id)
        except Exception as e:
            print(f"[CLICKUP-IMPORT] Fallo: {e}")
        finally:
            db.close()

    background_tasks.add_task(_do_import)
    
    return {
        "ok": True,
        "message": "La importaci?n ha comenzado en segundo plano. Esto puede tardar varios minutos dependiendo del volumen de datos."
    }

# =========================
# PROJECT MANAGEMENT API
# =========================

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: str = "TEAM_COLLABORATION"

class FolderCreate(BaseModel):
    name: str
    workspace_id: int

class ListCreate(BaseModel):
    name: str
    folder_id: Optional[int] = None
    workspace_id: int

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    list_id: Optional[int] = None
    assignee_id: Optional[int] = None
    priority: Optional[str] = None
    status: str = "to do"
    due_date: Optional[datetime] = None
    case_id: Optional[int] = None
    parent_id: Optional[int] = None
    
    class Config:
        extra = "ignore"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    case_id: Optional[int] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    assignee_ids: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    
    class Config:
        extra = "ignore"


class ChecklistItemCreate(BaseModel):
    content: str

class CommentCreate(BaseModel):
    task_id: int
    content: str

@app.get("/api/projects/workspaces")
@app.get("/projects/workspaces")
async def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna la jerarquia completa de espacios para el usuario."""
    if current_user.is_admin:
        workspaces = db.query(Workspace).options(
            joinedload(Workspace.folders).joinedload(Folder.lists)
        ).all()
        
        # Solo para modo local: si no hay espacios, crear un flujo local mínimo por defecto
        if not workspaces:
            print("[PROJECTS] Creando estructura basica de proyectos local...")
            ws = Workspace(name="Espacio Interno EMDECOB", visibility="TEAM_COLLABORATION", owner_id=current_user.id)
            db.add(ws)
            db.commit()
            db.refresh(ws)
            
            f = Folder(name="Proyectos y Casos", workspace_id=ws.id)
            db.add(f)
            db.commit()
            db.refresh(f)
            
            l = ProjectList(name="Tareas Pendientes", folder_id=f.id, workspace_id=ws.id)
            db.add(l)
            db.commit()
            
            workspaces = [ws]
    else:
        # User sees workspaces where they are member OR owner
        workspaces = db.query(Workspace).outerjoin(WorkspaceMember).filter(
            or_(
                Workspace.owner_id == current_user.id,
                WorkspaceMember.user_id == current_user.id
            )
        ).options(
            joinedload(Workspace.folders).joinedload(Folder.lists),
            joinedload(Workspace.lists)
        ).all()
    
    results = []
    for ws in workspaces:
        folders = []
        for f in ws.folders:
            lists = [{"id": l.id, "name": l.name} for l in f.lists]
            folders.append({"id": f.id, "name": f.name, "lists": lists})
        
        workspace_lists = [{"id": l.id, "name": l.name} for l in ws.lists]
        
        results.append({
            "id": ws.id,
            "name": ws.name,
            "visibility": ws.visibility,
            "clickup_id": ws.clickup_id,
            "folders": folders,
            "lists": workspace_lists
        })
    
    return results

@app.post("/api/projects/workspaces")
@app.post("/projects/workspaces")
async def create_workspace(
    ws_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        ws = Workspace(
            name=ws_data.name, 
            description=ws_data.description, 
            visibility=ws_data.visibility, 
            owner_id=current_user.id
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)
        return ws
    except Exception as e:
        db.rollback()
        print(f"[PROJECTS] Error creating workspace: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear espacio: {str(e)}")

class MemberAdd(BaseModel):
    user_id: int
    role: str = "VIEWER"

@app.post("/api/projects/workspaces/{workspace_id}/members")
@app.post("/projects/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: int,
    m_data: MemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar que el usuario actual es el dueño o admin
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace no encontrado")
        
    if ws.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permiso para agregar miembros")
        
    member = WorkspaceMember(workspace_id=workspace_id, user_id=m_data.user_id, role=m_data.role)
    db.add(member)
    db.commit()
    return {"ok": True}

@app.post("/api/projects/folders")
@app.post("/projects/folders")
async def create_folder(
    f_data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        f = Folder(name=f_data.name, workspace_id=f_data.workspace_id)
        db.add(f)
        db.commit()
        db.refresh(f)
        return f
    except Exception as e:
        db.rollback()
        print(f"[PROJECTS] Error creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear carpeta: {str(e)}")

@app.post("/api/projects/lists")
@app.post("/projects/lists")
async def create_list(
    l_data: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        l = ProjectList(
            name=l_data.name, 
            folder_id=l_data.folder_id, 
            workspace_id=l_data.workspace_id
        )
        db.add(l)
        db.commit()
        db.refresh(l)
        return l
    except Exception as e:
        db.rollback()
        print(f"[PROJECTS] Error creating list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear lista: {str(e)}")

@app.get("/api/cases/id/{case_id}/tasks")
@app.get("/cases/id/{case_id}/tasks")
async def get_tasks_by_case(case_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.case_id == case_id).all()
    return tasks

# Endpoint de diagnóstico público (sin auth) para verificar que el backend responde
@app.get("/debug/tasks")
async def debug_tasks(db: Session = Depends(get_db)):
    """Endpoint público sin auth para diagnóstico. NO usar en producción final."""
    try:
        tasks = db.query(Task).limit(5).all()
        total = db.query(Task).count()
        return {
            "ok": True,
            "total_tasks_in_db": total,
            "sample": [{"id": t.id, "title": t.title, "list_id": t.list_id, "status": t.status} for t in tasks]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/admin/bulk-import")
async def bulk_import(payload: dict, db: Session = Depends(get_db)):
    """
    Endpoint de importación masiva ONE-TIME.
    Recibe JSON con workspaces, folders, lists y tasks.
    Lo llama un script local que tiene acceso al PostgreSQL nativo.
    """
    import sqlalchemy as sa
    results = {}
    try:
        # 1. Workspaces
        for ws in payload.get("workspaces", []):
            db.execute(sa.text("""
                INSERT INTO workspaces (id, name, visibility, owner_id, clickup_id)
                VALUES (:id, :name, :vis, :oid, :cid)
                ON CONFLICT (id) DO NOTHING
            """), {"id": ws["id"], "name": ws["name"], "vis": ws.get("visibility","TEAM_COLLABORATION"),
                   "oid": ws.get("owner_id", 2), "cid": ws.get("clickup_id")})
        db.commit()
        results["workspaces"] = len(payload.get("workspaces", []))

        # 2. Folders
        for f in payload.get("folders", []):
            db.execute(sa.text("""
                INSERT INTO folders (id, name, workspace_id, clickup_id)
                VALUES (:id, :name, :wid, :cid)
                ON CONFLICT (id) DO NOTHING
            """), {"id": f["id"], "name": f["name"], "wid": f["workspace_id"], "cid": f.get("clickup_id")})
        db.commit()
        results["folders"] = len(payload.get("folders", []))

        # 3. Lists
        for l in payload.get("lists", []):
            db.execute(sa.text("""
                INSERT INTO project_lists (id, name, folder_id, workspace_id, clickup_id)
                VALUES (:id, :name, :fid, :wid, :cid)
                ON CONFLICT (id) DO NOTHING
            """), {"id": l["id"], "name": l["name"], "fid": l.get("folder_id"),
                   "wid": l.get("workspace_id"), "cid": l.get("clickup_id")})
        db.commit()
        results["lists"] = len(payload.get("lists", []))

        # 4. Tasks - insertamos sin case_id para evitar FK constraint con tabla cases vacía
        for t in payload.get("tasks", []):
            db.execute(sa.text("""
                INSERT INTO tasks (id, title, description, status, priority, assignee_id,
                                   list_id, due_date, case_id, parent_id, created_at, clickup_id)
                VALUES (:id, :title, :desc, :status, :priority, :aid,
                        :lid, :due, NULL, :pid, :cat, :clickup)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": t["id"], "title": t["title"], "desc": t.get("description"),
                "status": t.get("status","to do"), "priority": t.get("priority"),
                "aid": t.get("assignee_id"), "lid": t.get("list_id"),
                "due": t.get("due_date"),
                "pid": t.get("parent_id"), "cat": t.get("created_at"), "clickup": t.get("clickup_id")
            })
        db.commit()
        results["tasks"] = len(payload.get("tasks", []))


        return {"ok": True, "imported": results}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}

@app.get("/api/projects/tasks")
@app.get("/projects/tasks")
@app.get("/api/tasks")
@app.get("/tasks")
async def get_tasks(
    list_id: Optional[int] = None,
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    radicado: Optional[str] = None,
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task).options(
        selectinload(Task.subtasks),
        selectinload(Task.tags),
        selectinload(Task.attachments)
    )
    
    # Aplicar filtros adicionales
    if list_id:
        query = query.filter(Task.list_id == list_id)
    if case_id:
        query = query.filter(Task.case_id == case_id)
    if radicado:
        # Buscamos el caso por radicado exacto o LIKE
        case_subquery = db.query(Case.id).filter(Case.radicado.like(f"%{radicado}%")).scalar_subquery()
        query = query.filter(Task.case_id == case_subquery)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if status:
        query = query.filter(Task.status.ilike(f"%{status}%"))
        
    # Unimos con ProjectList para saber a qué workspace pertenece la tarea
    # Usamos outerjoin para asegurar que tareas sin lista (si existieran) no desaparezcan por error
    query = query.outerjoin(ProjectList, Task.list_id == ProjectList.id)
    query = query.outerjoin(Case, Task.case_id == Case.id)
    
    if current_user.is_admin and not current_user.company_id:
        # SuperAdmin ve todo sin restricciones
        pass
    else:
        # Filtro por Membresía de Workspace (Core de Colaboración)
        # El usuario debe ser dueño del workspace o miembro explícito
        user_workspaces_subquery = db.query(Workspace.id).outerjoin(WorkspaceMember).filter(
            or_(
                Workspace.owner_id == current_user.id,
                WorkspaceMember.user_id == current_user.id
            )
        ).scalar_subquery()
        
        # Filtro SaaS: Ve tareas asociadas a casos de su empresa, O en sus workspaces, O asignadas a él
        query = query.filter(
            or_(
                # Caso propio de su empresa
                and_(Task.case_id.isnot(None), Case.company_id == current_user.company_id),
                # Tarea sin caso pero en un workspace al que pertenece
                and_(Task.case_id.is_(None), ProjectList.workspace_id.in_(user_workspaces_subquery)),
                # Siempre ve lo que tiene asignado o lo que el sistema asocia a su ID directamente
                Task.assignee_id == current_user.id
            )
        )
        
    return query.order_by(desc(Task.created_at)).all()

# Control de concurrencia y prevención de bucles
clickup_sync_semaphore = None
_in_flight_syncs = set()

async def sync_task_with_clickup_background(task_id: int, api_token: str, user_id: int):
    """Sincroniza una tarea de ClickUp en segundo plano para evitar bloqueos y timeouts."""
    global clickup_sync_semaphore
    if clickup_sync_semaphore is None:
        clickup_sync_semaphore = asyncio.Semaphore(3)
        
    if task_id in _in_flight_syncs:
        print(f"[BG-CLICKUP] Sync ya está en progreso para tarea ID {task_id}, omitiendo.")
        return
        
    _in_flight_syncs.add(task_id)
    try:
        async with clickup_sync_semaphore:
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task or not task.clickup_id:
                    return
                    
                from backend.clickup_sync import fetch_clickup, process_task
                print(f"[BG-CLICKUP] Iniciando sync para tarea ID {task_id} (ClickUp {task.clickup_id})...")
                t_data = await fetch_clickup(f"task/{task.clickup_id}?include_subtasks=true&include_checklists=true", api_token)
                if t_data:
                    all_users = db.query(User).all()
                    user_map = { (u.nombre or '').lower().strip(): u.id for u in all_users if u.nombre }
                    user_map.update({ (u.username or '').lower().strip(): u.id for u in all_users })
                    
                    await process_task(t_data, task.list_id, db, user_id, user_map, api_token, inherited_case_id=task.case_id)
                    task.updated_at = now_colombia()
                    db.commit()
                    print(f"[BG-CLICKUP] Sync completado con exito para tarea ID {task_id}")
            except Exception as e:
                print(f"[BG-CLICKUP] Error sincronizando tarea {task_id} en segundo plano: {e}")
                db.rollback()
            finally:
                db.close()
    finally:
        _in_flight_syncs.discard(task_id)

@app.get("/api/tasks/{task_id}")
@app.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        from fastapi.responses import JSONResponse
        from datetime import datetime
        
        task = db.query(Task).options(
            selectinload(Task.subtasks),
            selectinload(Task.checklists),
            selectinload(Task.comments),
            selectinload(Task.tags),
            selectinload(Task.attachments)
        ).filter(Task.id == task_id).first()
        
        if not task:
            return JSONResponse(status_code=404, content={"detail": "Tarea no encontrada"})
        
        # Sincronización inteligente on-demand si es tarea de ClickUp
        if task.clickup_id:
            api_token = request.headers.get("X-ClickUp-Token")
            if api_token:
                is_fresh = False
                try:
                    age_seconds = (now_colombia() - task.updated_at).total_seconds()
                    if age_seconds < 120:
                        is_fresh = True
                        print(f" [TASK] Sirviendo tarea de ClickUp {task.clickup_id} desde BD local (fresca hace {age_seconds:.1f}s)")
                except Exception as age_err:
                    print(f" [TASK] Error calculando edad de la tarea: {age_err}")

                if not is_fresh:
                    print(f" [TASK] Lanzando sincronizacion en segundo plano para ClickUp task={task.clickup_id}")
                    # Usar asyncio.create_task normal, el semáforo se maneja dentro de la función
                    asyncio.create_task(sync_task_with_clickup_background(task.id, api_token, current_user.id))
        
        # Construcción manual segura para evitar recursividad infinita (Circular Reference)
        def fmt_dt(dt):
            if dt is None: return None
            return dt.isoformat() if isinstance(dt, datetime) else dt

        res_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": fmt_dt(task.due_date),
            "list_id": task.list_id,
            "assignee_id": task.assignee_id,
            "assignee_name": task.assignee_name,
            "creator_id": task.creator_id,
            "case_id": task.case_id,
            "parent_id": task.parent_id,
            "clickup_id": task.clickup_id,
            "created_at": fmt_dt(task.created_at),
            "updated_at": fmt_dt(task.updated_at),
            "subtasks": [
                {
                    "id": st.id,
                    "title": st.title,
                    "status": st.status,
                    "priority": st.priority,
                    "due_date": fmt_dt(st.due_date),
                    "assignee_name": st.assignee_name,
                    "parent_id": st.parent_id
                } for st in task.subtasks
            ],
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "user_id": c.user_id,
                    "user_name": c.user_name,
                    "created_at": fmt_dt(c.created_at)
                } for c in task.comments
            ],
            "tags": [{"name": t.name, "color": t.color} for t in task.tags],
            "checklists": [
                {
                    "id": cl.id,
                    "content": cl.content,
                    "is_completed": cl.is_completed
                } for cl in task.checklists
            ],
            "attachments": [
                {
                    "id": a.id,
                    "name": a.name,
                    "file_path": a.file_path,
                    "file_type": a.file_type
                } for a in task.attachments
            ]
        }
        
        return JSONResponse(content=res_data)
    except Exception as e:
        db.rollback()
        import traceback
        err_msg = f"Error: {str(e)}"
        print(f"[CRITICAL ERROR] get_task_detail: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"detail": err_msg})

@app.get("/cases/{case_id}/tasks")
async def get_case_tasks_endpoint(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna las tareas vinculadas a un radicado espec?fico."""
    q = db.query(Task).filter(Task.case_id == case_id)
    
    # Seguridad: Si no es admin, verificar que el caso le pertenezca o esté asignado
    if not current_user.is_admin:
        q = q.join(Case, Task.case_id == Case.id)
        q = q.filter(or_(
            Case.user_id == current_user.id,
            Task.assignee_id == current_user.id
        ))

    return q.order_by(desc(Task.created_at)).all()

@app.post("/api/projects/tasks")
@app.post("/projects/tasks")
@app.post("/api/tasks")
@app.post("/tasks")
async def create_task(
    t_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lid = t_data.list_id
    list_exists = False
    if lid is not None:
        list_exists = db.query(ProjectList).filter(ProjectList.id == lid).count() > 0
        
    if not list_exists:
        # Intentar buscar lista del abogado del caso
        if t_data.case_id:
            case_obj = db.query(Case).filter(Case.id == t_data.case_id).first()
            if case_obj and case_obj.abogado:
                # Buscar lista que coincida con el nombre del abogado
                lawyer_list = db.query(ProjectList).filter(ProjectList.name.ilike(f"%{case_obj.abogado}%")).first()
                if lawyer_list:
                    lid = lawyer_list.id
                    list_exists = True
                    print(f" [TASK] Reasignando list_id invalido ({t_data.list_id}) a la lista del abogado: {lawyer_list.name} (ID {lid})")
        
        if not list_exists:
            # Buscar "BANDEJA DE ENTRADA" o similar
            default_list = db.query(ProjectList).filter(ProjectList.name.ilike("%bandeja%")).first()
            if not default_list:
                default_list = db.query(ProjectList).first()
            
            if default_list:
                lid = default_list.id
                list_exists = True
                print(f" [TASK] Reasignando list_id invalido ({t_data.list_id}) a la lista por defecto: {default_list.name} (ID {lid})")
            else:
                raise HTTPException(status_code=400, detail="No existe ninguna lista de proyectos en la base de datos para asignar la tarea.")

    print(f"[DEBUG] Creating task: title={t_data.title}, parent_id={t_data.parent_id}, case_id={t_data.case_id}")
    try:
        task = Task(
            title=t_data.title,
            description=t_data.description,
            list_id=lid,
            assignee_id=t_data.assignee_id,
            priority=t_data.priority,
            status=(t_data.status or "ABIERTO").upper(),
            due_date=t_data.due_date,
            case_id=t_data.case_id,
            parent_id=t_data.parent_id,
            creator_id=current_user.id
        )
        
        # Auditoría de identidad: Poblar assignee_name automáticamente
        if t_data.assignee_id:
            user_obj = db.query(User).filter(User.id == t_data.assignee_id).first()
            if user_obj:
                task.assignee_name = user_obj.nombre or user_obj.username
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[CRITICAL ERROR] create_task: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/projects/tasks/{task_id}")
@app.delete("/projects/tasks/{task_id}")
@app.delete("/api/tasks/{task_id}")
@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    try:
        # Eliminar subtareas primero
        subtasks = db.query(Task).filter(Task.parent_id == task_id).all()
        for st in subtasks:
            db.query(TaskComment).filter(TaskComment.task_id == st.id).delete()
            db.query(TaskChecklistItem).filter(TaskChecklistItem.task_id == st.id).delete()
            db.delete(st)
        
        # Eliminar comentarios, checklists y attachments de la tarea padre
        db.query(TaskComment).filter(TaskComment.task_id == task_id).delete()
        db.query(TaskChecklistItem).filter(TaskChecklistItem.task_id == task_id).delete()
        db.query(TaskAttachment).filter(TaskAttachment.task_id == task_id).delete()
        
        db.delete(task)
        db.commit()
        print(f"[TASK] Tarea {task_id} eliminada por usuario {current_user.username}")
        return {"ok": True, "detail": "Tarea eliminada correctamente"}
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[CRITICAL ERROR] delete_task: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/projects/tasks/{task_id}/comments")
@app.post("/api/projects/tasks/{task_id}/comments")
@app.post("/api/tasks/{task_id}/comments")
@app.post("/tasks/{task_id}/comments")
async def add_task_comment(
    task_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = TaskComment(
        task_id=task_id,
        content=data.get("content"),
        user_id=current_user.id,
        user_name=current_user.nombre or current_user.username
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@app.post("/projects/tasks/{task_id}/checklists")
@app.post("/api/projects/tasks/{task_id}/checklists")
@app.post("/api/tasks/{task_id}/checklists")
@app.post("/tasks/{task_id}/checklists")
async def add_task_checklist_item(
    task_id: int,
    data: ChecklistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = TaskChecklistItem(
        task_id=task_id,
        content=data.content,
        is_completed=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.delete("/api/tasks/comments/{comment_id}")
@app.delete("/tasks/comments/{comment_id}")
async def delete_task_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    
    # Solo admin o el creador pueden borrar
    if not current_user.is_admin and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar este comentario")
        
    db.delete(comment)
    db.commit()
    return {"ok": True}

@app.patch("/api/tasks/comments/{comment_id}")
@app.patch("/tasks/comments/{comment_id}")
async def update_task_comment(comment_id: int, data: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    
    if not current_user.is_admin and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este comentario")
        
    comment.content = data.get("content", comment.content)
    db.commit()
    return comment

@app.patch("/api/tasks/checklists/{item_id}")
@app.patch("/tasks/checklists/{item_id}")
async def update_task_checklist_item(item_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(TaskChecklistItem).filter(TaskChecklistItem.id == item_id).first()
    if not item: raise HTTPException(status_code=404)
    if "content" in data: item.content = data["content"]
    if "is_completed" in data: item.is_completed = data["is_completed"]
    db.commit()
    return item

@app.delete("/api/tasks/checklists/{item_id}")
@app.delete("/tasks/checklists/{item_id}")
async def delete_task_checklist_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(TaskChecklistItem).filter(TaskChecklistItem.id == item_id).first()
    if not item: raise HTTPException(status_code=404)
    db.delete(item)
    db.commit()
    return {"ok": True}


@app.patch("/api/projects/tasks/{task_id}")
@app.patch("/projects/tasks/{task_id}")
@app.put("/api/projects/tasks/{task_id}")
@app.put("/projects/tasks/{task_id}")
@app.patch("/api/tasks/{task_id}")
@app.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    t_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    try:
        if t_data.title is not None: task.title = t_data.title
        if t_data.description is not None: task.description = t_data.description
        if t_data.status is not None: task.status = t_data.status.upper()
        if hasattr(t_data, 'case_id') and t_data.case_id is not None: task.case_id = t_data.case_id
        
        # Auditoría de identidad: Sincronizar nombre si cambia el ID
        if t_data.assignee_id is not None:
            user_obj = db.query(User).filter(User.id == t_data.assignee_id).first()
            if user_obj:
                task.assignee_name = user_obj.nombre or user_obj.username
        
        if hasattr(t_data, 'assignee_ids') and t_data.assignee_ids is not None:
            db_users = db.query(User).filter(User.id.in_(t_data.assignee_ids)).all()
            task.assignees = db_users
            if db_users:
                task.assignee_id = db_users[0].id
                task.assignee_name = ", ".join([(u.nombre or u.username) for u in db_users])
        
        if hasattr(t_data, 'tags') and t_data.tags is not None:
            # t_data.tags es una lista de nombres de tags
            db_tags = []
            for tname in t_data.tags:
                tag = db.query(Tag).filter(Tag.name == tname).first()
                if not tag:
                    tag = Tag(name=tname)
                    db.add(tag)
                    db.flush()
                db_tags.append(tag)
            task.tags = db_tags

        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[CRITICAL ERROR] update_task {task_id}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    # Endpoint consolidado en la l?nea 3604
    pass

@app.get("/cases/{id}/tasks")
async def get_case_tasks(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tasks = db.query(Task).filter(Task.case_id == id).order_by(desc(Task.created_at)).all()
    return [{
        "id": t.id,
        "title": t.title,
        "status": t.status,
        "priority": t.priority,
        "assignee_id": t.assignee_id,
        "list_id": t.list_id,
        "due_date": t.due_date,
        "parent_id": t.parent_id,
        "created_at": t.created_at
    } for t in tasks]

# =========================
# ADVANCED DASHBOARD & INLINE EDIT
# =========================

@app.get("/cases/stats/dashboard")
async def get_advanced_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene estad?sticas de negocio para las etiquetas superiores."""
    hoy = today_colombia()
    ayer = hoy - timedelta(days=1)
    
    # 1. Conteo de actuaciones en el mes actual
    first_of_month_str = hoy.replace(day=1).strftime("%Y-%m-%d")
    q_month = db.query(CaseEvent).filter(CaseEvent.event_date >= first_of_month_str)
    
    if current_user.is_admin and not current_user.company_id:
        pass
    else:
        q_month = q_month.join(Case, CaseEvent.case_id == Case.id).filter(Case.company_id == current_user.company_id)
        
    month_actions = q_month.with_entities(func.count(func.distinct(CaseEvent.case_id))).scalar()
    
    # 2. Conteo de casos por Abogado (desglose)
    q_abogados = db.query(Case.abogado, func.count(Case.id)).filter(Case.abogado.isnot(None), Case.abogado != "")
    if current_user.is_admin and not current_user.company_id:
        pass
    else:
        q_abogados = q_abogados.filter(Case.company_id == current_user.company_id)
    
    lawyer_counts = q_abogados.group_by(Case.abogado).all()
    lawyer_stats = [{"name": l[0], "count": l[1]} for l in lawyer_counts]
    
    # 3. Alertas (casos sin leer)
    q_unread = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
        )
    )
    if current_user.is_admin and not current_user.company_id:
        pass
    else:
        q_unread = q_unread.filter(Case.company_id == current_user.company_id)
        
    unread_total = q_unread.count()
    
    return {
        "month_actions": month_actions,
        "month_name": hoy.strftime("%B"),
        "lawyer_stats": lawyer_stats,
        "unread_total": unread_total
    }

class LawyerUpdate(BaseModel):
    abogado: str

@app.patch("/cases/{case_id}/lawyer")
async def update_case_lawyer(
    case_id: int,
    data: LawyerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizaci?n ultra-r?pida del abogado para edici?n en l?nea."""
    cs = db.query(Case).filter(Case.id == case_id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    cs.abogado = data.abogado
    # Intentar buscar el usuario por nombre para sincronizar user_id autom?ticamente
    match_user = db.query(User).filter(User.nombre.ilike(f"%{data.abogado}%")).first()
    if match_user:
        cs.user_id = match_user.id
        
    db.commit()
    return {"ok": True, "abogado": cs.abogado, "user_id": cs.user_id}

# =========================
# INTEGRACIONES EXTERNAS (CALLY, ETC)
# =========================

def verify_cally_key(api_key: str):
    """Dependency to verify Cally API Key"""
    db = SessionLocal()
    try:
        config = db.query(IntegrationConfig).filter(
            IntegrationConfig.service_name == 'cally',
            IntegrationConfig.api_key == api_key,
            IntegrationConfig.is_active == True
        ).first()
        if not config:
            raise HTTPException(status_code=401, detail="Clave de API de Cally inv?lida")
        return config
    finally:
        db.close()

@app.get("/api/config/integrations")
async def get_integrations_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """(Admin) Obtiene las claves de integraci?n externas."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    config = db.query(IntegrationConfig).filter(IntegrationConfig.service_name == 'cally').first()
    if not config:
        # Inicializar si no existe
        import secrets
        new_key = f"cally_{secrets.token_urlsafe(32)}"
        config = IntegrationConfig(service_name='cally', api_key=new_key)
        db.add(config)
        db.commit()
        db.refresh(config)
        
    return {
        "service_name": "cally",
        "api_key": config.api_key,
        "is_active": config.is_active,
        "report_url": "/api/external/reporting/tasks"
    }

@app.post("/api/config/integrations/regenerate")
async def regenerate_cally_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """(Admin) Regenera la clave de Cally."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    import secrets
    config = db.query(IntegrationConfig).filter(IntegrationConfig.service_name == 'cally').first()
    new_key = f"cally_{secrets.token_urlsafe(32)}"
    
    if not config:
        config = IntegrationConfig(service_name='cally', api_key=new_key)
        db.add(config)
    else:
        config.api_key = new_key
    
    db.commit()
    return {"api_key": new_key}

# =========================
# MODULO SUPERADMIN: EMPRESAS Y USUARIOS
# =========================

class CompanyCreateRequest(BaseModel):
    nombre: str
    nit: Optional[str] = None
    limite_usuarios: int = 5

class UserCreateRequest(BaseModel):
    username: str
    password: str
    nombre: str
    company_id: Optional[int] = None
    email: Optional[str] = None
    is_admin: bool = False

@app.get("/admin/companies")
async def get_admin_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
    
    comps = db.query(Company).order_by(Company.id.desc()).all()
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "nit": c.nit,
            "estado": c.estado or "activo",
            "limite_usuarios": c.limite_usuarios,
            "payment_status": getattr(c, 'payment_status', 'al_dia') or 'al_dia',
            "suspension_reason": getattr(c, 'suspension_reason', None),
            "suspended_at": str(c.suspended_at) if getattr(c, 'suspended_at', None) else None,
            "suspended_by": getattr(c, 'suspended_by', None),
            "reactivated_at": str(c.reactivated_at) if getattr(c, 'reactivated_at', None) else None,
            "last_payment_date": str(c.last_payment_date) if getattr(c, 'last_payment_date', None) else None,
            "next_payment_due": str(c.next_payment_due) if getattr(c, 'next_payment_due', None) else None,
            "billing_notes": getattr(c, 'billing_notes', None),
            "created_at": str(c.created_at) if getattr(c, 'created_at', None) else None,
        }
        for c in comps
    ]

@app.post("/admin/companies")
async def create_admin_company(
    data: CompanyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
    
    comp = Company(nombre=data.nombre, nit=data.nit, limite_usuarios=data.limite_usuarios, estado='activo')
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return {
        "id": comp.id,
        "nombre": comp.nombre,
        "nit": comp.nit,
        "estado": comp.estado or "activo",
        "limite_usuarios": comp.limite_usuarios,
        "payment_status": getattr(comp, 'payment_status', 'al_dia') or 'al_dia',
        "suspension_reason": None,
        "suspended_at": None,
        "suspended_by": None,
        "reactivated_at": None,
        "last_payment_date": None,
        "next_payment_due": None,
        "billing_notes": None,
        "created_at": str(comp.created_at) if getattr(comp, 'created_at', None) else None,
    }

@app.get("/admin/users")
async def get_admin_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
    
    users = db.query(User).order_by(User.id.desc()).all()
    return [{"id": u.id, "username": u.username, "nombre": u.nombre, "company_id": u.company_id, "is_admin": u.is_admin} for u in users]

@app.post("/admin/users")
async def create_admin_user(
    data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
    
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    new_user = User(
        username=data.username,
        hashed_password=pwd_context.hash(data.password),
        nombre=data.nombre,
        company_id=data.company_id,
        email=data.email,
        is_admin=data.is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "nombre": new_user.nombre, "company_id": new_user.company_id, "is_admin": new_user.is_admin}

class CompanySuspendRequest(BaseModel):
    reason: str
    notes: Optional[str] = None

class CompanyReactivateRequest(BaseModel):
    notes: Optional[str] = None

@app.post("/admin/companies/{company_id}/suspend")
async def suspend_company(
    company_id: int,
    data: CompanySuspendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    
    comp = db.query(Company).filter(Company.id == company_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")
        
    comp.estado = "suspendida_pago"
    comp.payment_status = "suspendido"
    comp.suspended_at = datetime.utcnow()
    comp.suspended_by = current_user.id
    comp.suspension_reason = data.reason
    if data.notes:
        comp.billing_notes = data.notes
        
    db.commit()
    db.refresh(comp)
    return {"ok": True, "message": "Empresa suspendida exitosamente."}

@app.post("/admin/companies/{company_id}/reactivate")
async def reactivate_company(
    company_id: int,
    data: CompanyReactivateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    
    comp = db.query(Company).filter(Company.id == company_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")
        
    comp.estado = "activo"
    comp.payment_status = "al_dia"
    comp.reactivated_at = datetime.utcnow()
    comp.reactivated_by = current_user.id
    comp.last_payment_date = datetime.utcnow()
    if data.notes:
        comp.billing_notes = data.notes
        
    db.commit()
    db.refresh(comp)
    return {"ok": True, "message": "Empresa reactivada exitosamente."}

@app.post("/admin/companies/{company_id}/mark-overdue")
async def mark_overdue_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    
    comp = db.query(Company).filter(Company.id == company_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")
        
    comp.payment_status = "en_mora"
    db.commit()
    db.refresh(comp)
    return {"ok": True, "message": "Empresa marcada en mora."}

# =========================
# MODULO SUPERADMIN: SIMULADOR DE FACTURACION
# =========================

@app.get("/admin/billing/tiers")
async def get_billing_tiers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
    
    tiers = db.query(BillingTier).order_by(BillingTier.min_cases).all()
    return {"ok": True, "tiers": [
        {"id": t.id, "min_cases": t.min_cases, "max_cases": t.max_cases, "price": t.price}
        for t in tiers
    ]}

@app.post("/admin/billing/tiers")
async def update_billing_tiers(
    data: BillingTierUpdateList,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
    
    # Delete all and recreate
    db.query(BillingTier).delete()
    
    for tier in data.tiers:
        db.add(BillingTier(
            min_cases=tier.min_cases,
            max_cases=tier.max_cases,
            price=tier.price
        ))
    db.commit()
    
    return {"ok": True, "message": "Rangos de facturación actualizados."}

@app.get("/admin/billing/simulator")
async def get_billing_simulator(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")
        
    companies = db.query(Company).filter(Company.estado.notin_(['suspendida_pago', 'inactiva'])).all()
    tiers = db.query(BillingTier).order_by(BillingTier.min_cases).all()
    
    results = []
    for comp in companies:
        users_count = db.query(User).filter(User.company_id == comp.id).count()
        # Se cuenta is_active=True (usamos los campos genericos si is_active falla usamos todos)
        active_cases = db.query(Case).filter(Case.company_id == comp.id).count() 
        
        applicable_tier = None
        base_price = 0
        
        for tier in tiers:
            if active_cases >= tier.min_cases and (tier.max_cases is None or active_cases <= tier.max_cases):
                applicable_tier = f"{tier.min_cases} - {tier.max_cases if tier.max_cases else 'Adelante'}"
                base_price = tier.price
                break
                
        results.append({
            "company_id": comp.id,
            "company_name": comp.nombre,
            "users_count": users_count,
            "active_cases": active_cases,
            "applicable_tier": applicable_tier or "Sin rango",
            "total_cost": base_price
        })
        
    return {"ok": True, "simulator": results}

@app.get("/v1/system/health")
async def system_health_diagnostic(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Diagn?stico senior para detectar bloqueos y estado de base de datos."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403)
        
    case_count = db.query(Case).count()
    task_count = db.query(Task).count()
    id_proceso_count = db.query(Case).filter(Case.id_proceso.isnot(None)).count()
    
    # Probar conexi?n Rama Judicial (petici?n m?nima)
    rama_status = "OK"
    try:
        from backend.service.rama import _get
        await _get("/Procesos/Detalle/1") # ID ficticio pero v?lido para test
    except RamaRateLimitError:
        rama_status = "BLOQUEADO (403)"
    except Exception as e:
        rama_status = f"ERROR: {str(e)}"
        
    return {
        "version": "4.0.0-SENIOR",
        "database": {
            "cases": case_count,
            "tasks": task_count,
            "cases_synchronized": id_proceso_count
        },
        "integrations": {
            "rama_judicial": rama_status,
            "clickup": "Configurada" # Asumimos si el endpoint responde
        },
        "server_time": now_colombia()
    }

@app.get("/api/projects/tags")
@app.get("/projects/tags")
async def get_all_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna todas las etiquetas del sistema."""
    return db.query(Tag).all()

@app.get("/api/projects/statuses")
@app.get("/projects/statuses")
async def get_all_statuses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna todos los estados ?nicos usados en el sistema."""
    statuses = db.query(Task.status).filter(Task.status.isnot(None)).distinct().all()
    # Agregar estados base por defecto si no existen
    base_statuses = ['ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'NOT PERSONAL', 'LIQUIDACION', 'REMATE', 'COMPLETO', 'CLOSED']
    current_list = [s[0].upper() for s in statuses if s[0]]
    final_list = list(set(current_list + base_statuses))
    return sorted(final_list)


# =========================
# ADMIN PANEL (DJANGO-LIKE)
# =========================

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and _verify_password(password, user.hashed_password) and user.is_admin:
                request.session.update({"token": create_access_token(user.id)})
                return True
        finally:
            db.close()
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        token = request.session.get("token")
        if not token:
            return RedirectResponse(request.url_for("admin:login"))
        user_id = verify_access_token(token)
        if not user_id:
            return RedirectResponse(request.url_for("admin:login"))
        # Verificar si sigue siendo admin y activo
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_admin or not user.is_active:
                request.session.clear()
                return RedirectResponse(request.url_for("admin:login"))
        finally:
            db.close()
        return None

authentication_backend = AdminAuth(secret_key=secrets.token_urlsafe(32))
admin = Admin(app, engine, authentication_backend=authentication_backend, base_url="/admin", title="EMDECOB - Panel Admin")

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.nombre, User.email, User.is_admin, User.is_active]
    column_searchable_list = [User.username, User.nombre, User.email]
    column_filters = [User.is_admin, User.is_active]
    name = "Usuario"
    name_plural = "Usuarios"
    icon = "fa-solid fa-user"

class CaseAdmin(ModelView, model=Case):
    column_list = [Case.id, Case.radicado, Case.demandante, Case.demandado, Case.abogado]
    column_searchable_list = [Case.radicado, Case.demandante, Case.demandado, Case.abogado]
    column_filters = [Case.user_id]
    name = "Radicado"
    name_plural = "Radicados"
    icon = "fa-solid fa-folder-open"

class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.title, Task.status, Task.priority, Task.due_date, Task.assignee_name]
    column_searchable_list = [Task.title, Task.status, Task.assignee_name]
    column_filters = [Task.status, Task.priority]
    name = "Tarea"
    name_plural = "Tareas"
    icon = "fa-solid fa-list-check"

class WorkspaceAdmin(ModelView, model=Workspace):
    column_list = [Workspace.id, Workspace.name, Workspace.visibility]
    name = "Espacio"
    name_plural = "Espacios"
    icon = "fa-solid fa-briefcase"

class IntegrationAdmin(ModelView, model=IntegrationConfig):
    column_list = [IntegrationConfig.id, IntegrationConfig.service_name, IntegrationConfig.is_active]
    name = "Integraci?n"
    name_plural = "Integraciones"
    icon = "fa-solid fa-plug"

admin.add_view(UserAdmin)
admin.add_view(CaseAdmin)
admin.add_view(TaskAdmin)
admin.add_view(WorkspaceAdmin)
admin.add_view(IntegrationAdmin)
