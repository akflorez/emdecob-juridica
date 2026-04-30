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
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, sessionmaker, joinedload
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
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

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

from backend.models import (
    Case, CaseEvent, NotificationConfig, NotificationLog, InvalidRadicado, 
    User, CasePublication, SearchJob, Workspace, WorkspaceMember, Folder, 
    ProjectList, Task, TaskComment, TaskChecklistItem, TaskAttachment, IntegrationConfig
)
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
from backend.service.publicaciones import consultar_publicaciones, parse_fecha_pub, consultar_publicaciones_rango
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
            print(f"[flush-loop] Error: {e}")


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
    
    return user


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
        
        u2 = db.query(User).filter(User.username == "jurico_emdecob").first()
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
# HOME
# =========================
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
    return {"version": "afc9789f5e68060483ce72910d7b73ab3cada7f0", "database": "juricob"}

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

    if not current_user.is_admin:
        if current_user.username in ["jurico_emdecob", "jurico.emdecob"]:
            q_validos = q_validos.filter(Case.user_id == current_user.id)
            q_invalidos = q_invalidos.filter(InvalidRadicado.user_id == current_user.id)
            q_pendientes = q_pendientes.filter(Case.user_id == current_user.id)
        else:
            emdecob_user = db.query(User).filter(User.username.in_(["jurico_emdecob", "jurico.emdecob"])).first()
            if emdecob_user:
                q_validos = q_validos.filter(or_(Case.user_id != emdecob_user.id, Case.user_id.is_(None)))
                q_invalidos = q_invalidos.filter(or_(InvalidRadicado.user_id != emdecob_user.id, InvalidRadicado.user_id.is_(None)))
                q_pendientes = q_pendientes.filter(or_(Case.user_id != emdecob_user.id, Case.user_id.is_(None)))

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

    if not current_user.is_admin:
        if current_user.username in ["jurico_emdecob", "jurico.emdecob"]:
            q_no_leidos = q_no_leidos.filter(Case.user_id == current_user.id)
            q_hoy = q_hoy.filter(Case.user_id == current_user.id)
        else:
            emdecob_user = db.query(User).filter(User.username.in_(["jurico_emdecob", "jurico.emdecob"])).first()
            if emdecob_user:
                q_no_leidos = q_no_leidos.filter(or_(Case.user_id != emdecob_user.id, Case.user_id.is_(None)))
                q_hoy = q_hoy.filter(or_(Case.user_id != emdecob_user.id, Case.user_id.is_(None)))

    total_no_leidos = q_no_leidos.count()
    total_actualizados_hoy = q_hoy.count()

    return {
        "total_validos": total_validos,
        "total_invalidos": total_invalidos,
        "total_pendientes": total_pendientes,
        "total_no_leidos": total_no_leidos,
        "total_actualizados_hoy": total_actualizados_hoy,
    }


# =========================
# AUTH  LOGIN / LOGOUT / USUARIOS
# =========================

@app.post("/auth/login")
def login(data: LoginRequest):
    """Autentica un usuario y retorna un token de sesi?n."""

    # 1. Intentar identificaci?n por Hardcoded Users primero para rapidez y resiliencia
    hc = HARDCODED_USERS.get(data.username)
    
    # 2. Intentar contra la base de datos
    db = None
    user_db = None
    try:
        db = SessionLocal()
        user_db = db.query(User).filter(
            User.username == data.username,
            User.is_active == True
        ).first()
        
        if user_db and _verify_password(data.password, user_db.hashed_password):
            token = create_access_token(user_db.id)
            return {
                "token": token,
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
            "token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": data.username,
                "nombre": hc["nombre"],
                "is_admin": hc["is_admin"],
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
    q = db.query(Case)

    # Multi-tenancy filter
    if not current_user.is_admin:
        if current_user.username in ["jurico_emdecob", "jurico.emdecob"]:
            # EMDECOB solo ve sus casos VALIDOS (con juzgado)
            q = q.filter(Case.user_id == current_user.id, Case.juzgado.isnot(None))
        else:
            emdecob_user = db.query(User).filter(User.username.in_(["jurico_emdecob", "jurico.emdecob"])).first()
            if emdecob_user:
                q = q.filter(or_(Case.user_id != emdecob_user.id, Case.user_id.is_(None)))

    # Default filtering logic:
    # If explicit filters are provided, follow them.
    # Otherwise, if it's a standard user with NO valid cases but has pending cases, 
    # we default to showing pending cases instead of an empty valid list.
    
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

    if not current_user.is_admin:
        if current_user.username in ["jurico_emdecob", "jurico.emdecob"]:
            q_unread = q_unread.filter(Case.user_id == current_user.id)
        else:
            emdecob_user = db.query(User).filter(User.username.in_(["jurico_emdecob", "jurico.emdecob"])).first()
            if emdecob_user:
                q_unread = q_unread.filter(or_(Case.user_id != emdecob_user.id, Case.user_id.is_(None)))
    
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
    q = db.query(Case).filter(Case.juzgado.isnot(None))

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
            "Cdula": c.cedula or "",
            "Abogado": c.abogado or "",
            "Juzgado": c.juzgado or "",
            "Fecha Radicacin": c.fecha_radicacion.isoformat() if c.fecha_radicacion else "",
            "ltima Actuacin": c.ultima_actuacion.isoformat() if c.ultima_actuacion else "",
            "ltima Verificacin": c.last_check_at.strftime("%Y-%m-%d %H:%M") if c.last_check_at else "",
            "Estado": "No ledo" if is_unread_case(c) else "Ledo",
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
    }

@app.get("/cases/id/{case_id}")
async def get_case_by_id_prefixed(case_id: int, db: Session = Depends(get_db)):
    return await get_case_by_id(case_id, db)

@app.get("/cases/by-radicado/{radicado}")
async def get_case_by_radicado(radicado: str, db: Session = Depends(get_db)):
    try:
        r = clean_str(radicado)
        if not r:
            raise HTTPException(400, "Radicado requerido")

        try:
            resp = await consulta_por_radicado(r, solo_activos=False, pagina=1)
        except RamaError as e:
            raise HTTPException(502, f"Error Rama Judicial: {str(e)}")

        items = extract_items(resp)
        if not items:
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
            })

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
        radicado = case.radicado
        fecha_act = item_act.get("event_date") # "YYYY-MM-DD"
        
        pubs = await consultar_publicaciones_rango(radicado, fecha_act, case.demandado or "")
        
        if pubs:
            for p in pubs:
                f_pub = parse_fecha_pub(p.get("fecha"))
                exists = db_session.query(CasePublication).filter(CasePublication.source_id == p.get("source_id")).first()
                if not exists:
                    db_session.add(CasePublication(
                        case_id=case.id,
                        fecha_publicacion=f_pub,
                        tipo_publicacion=p.get("tipo"),
                        descripcion=p.get("descripcion"),
                        documento_url=p.get("documento_url"),
                        source_url=p.get("source_url"),
                        source_id=p.get("source_id")
                    ))
            db_session.commit()
            print(f"[sync-pub] {len(pubs)} publicaciones sincronizadas para {radicado}")
    except Exception as e:
        print(f"[sync-pub] Error sincronizando publicaciones: {e}")

@app.get("/cases/by-radicado/{radicado}")
async def get_case_by_radicado_endpoint(radicado: str, db: Session = Depends(get_db)):
    """
    Busca un caso por radicado. Primero en BD local, luego en Rama Judicial.
    Esto alimenta la p?gina de 'Consultar Caso'.
    """
    r = clean_str(radicado)
    if not r:
        raise HTTPException(400, "Radicado inv?lido")

    # 1. Buscar en BD local
    existing_items = db.query(Case).filter(Case.radicado == r).all()
    if existing_items:
        # Aplicar el mismo filtro de FNA/TRIADA a los resultados locales
        local_results = []
        for c in existing_items:
            if _es_fna(c.demandante or ""):
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
        
        # FILTRO DIN?MICO: Preferir FNA o TRIADA, pero mostrar otros si no hay coincidencias
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
async def get_events_by_id(case_id: int, db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(404, "Caso no encontrado")
    return await events_logic(c, db)

@app.get("/api/cases/by-radicado/{radicado}/events")
@app.get("/cases/by-radicado/{radicado}/events")
@app.get("/api/cases/{radicado}/events")
@app.get("/cases/{radicado}/events")
async def get_events_by_radicado_unified(radicado: str, db: Session = Depends(get_db)):
    r = clean_str(radicado)
    # Si es un numero corto, intentarlo como ID por si acaso el frontend se equivoca
    if r.isdigit() and len(r) < 10:
        c = db.query(Case).filter(Case.id == int(r)).first()
        if c: return await events_logic(c, db)
    
    c = db.query(Case).filter(Case.radicado == r).order_by(Case.id.desc()).first()
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
        
        # 1. Obtener datos locales actuales
        db_events = db.query(CaseEvent).filter(CaseEvent.case_id == c.id).order_by(desc(CaseEvent.created_at)).all()
        
        # 2. Decidir si necesitamos refrescar (en segundo plano)
        # Si no hay eventos o el ultimo check fue hace mas de 12 horas
        needs_refresh = False
        if not db_events:
            needs_refresh = True
        elif not c.last_check_at or (now_colombia() - c.last_check_at).total_seconds() > 43200:
            needs_refresh = True
            
        if needs_refresh:
            print(f"[SYNC] Disparando actualizacion para {radicado}")
            # Si no hay eventos, lo hacemos Sincrono la primera vez para que el usuario vea algo
            if not db_events:
                await sync_case_events_background(c.id)
                # Volver a consultar
                db_events = db.query(CaseEvent).filter(CaseEvent.case_id == c.id).order_by(desc(CaseEvent.created_at)).all()
            else:
                asyncio.create_task(sync_case_events_background(c.id))

        # 3. Formatear para el frontend
        result_items = []
        for e in db_events:
            result_items.append({
                "id_reg_actuacion": None, # No lo tenemos si solo es local
                "cons_actuacion": None,
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

        new_count = 0
        for a in acts:
            it = {
                "event_date": a.get("fechaActuacion"),
                "title": (a.get("actuacion") or "").strip(),
                "detail": a.get("anotacion"),
            }
            event_hash = sha256_obj(it)
            exists = db.query(CaseEvent).filter(CaseEvent.case_id == c.id, CaseEvent.event_hash == event_hash).first()
            if not exists:
                con_docs = bool(a.get("conDocumentos"))
                db.add(CaseEvent(
                    case_id=c.id,
                    event_date=it["event_date"],
                    title=it["title"],
                    detail=it["detail"],
                    event_hash=event_hash,
                    con_documentos=con_docs,
                ))
                if con_docs: c.has_documents = True
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
                existing_cases = db.query(Case).filter(Case.radicado == radicado).all()
                
                if existing_cases:
                    for c in existing_cases:
                        c.cedula = cedula or c.cedula
                        c.abogado = abogado or c.abogado
                    updated += 1
                else:
                    # Si ya estaba marcado como invlido, lo removemos para que vuelva a intentar validarse
                    existing_invalid = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == radicado).first()
                    if existing_invalid:
                        db.delete(existing_invalid)
                        db.flush()

                    db.add(Case(radicado=radicado, cedula=cedula, abogado=abogado, user_id=current_user.id))
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
    llave_proceso: str = Query(..., description="La llave (radicado) del proceso de 23 dgitos")
):
    print(f"\n [DOCS] id_reg_actuacion={id_reg_actuacion} | llave_proceso={llave_proceso}")

    items = []

    try:
        raw = await documentos_actuacion(id_reg_actuacion, llave_proceso)
        print(f" [DOCS] service/rama.documentos_actuacion()  tipo={type(raw).__name__} | valor={str(raw)[:300]}")
        items = extract_documentos_from_response(raw)
        print(f" [DOCS] items extrados del servicio: {len(items)}")
    except RamaError as e:
        print(f" [DOCS] RamaError en servicio: {e}")
    except Exception as e:
        print(f" [DOCS] Error en servicio: {e}")
        traceback.print_exc()

    if not items:
        print(f" [DOCS] Servicio retorn vaco. Intentando llamada directa a Rama Judicial...")
        try:
            items = await fetch_documentos_rama_directa(id_reg_actuacion, llave_proceso)
            print(f" [DOCS] items desde llamada directa: {len(items)}")
        except Exception as e:
            print(f" [DOCS] Error en llamada directa: {e}")
            traceback.print_exc()

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
        client = httpx.AsyncClient(timeout=60.0, verify=False, headers=RAMA_HEADERS)
        response = await client.send(
            client.build_request("GET", url_rama),
            stream=True
        )

        print(f" Status Rama Judicial: {response.status_code}")

        if response.status_code != 200:
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
async def get_case_publications(radicado: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.radicado == radicado).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
        
    pubs = db.query(CasePublication).filter(CasePublication.case_id == case.id).order_by(desc(CasePublication.fecha_publicacion)).all()
    return {
        "items": [
            {
                "id": p.id,
                "fecha_publicacion": p.fecha_publicacion.isoformat() if p.fecha_publicacion else None,
                "tipo_publicacion": p.tipo_publicacion,
                "descripcion": p.descripcion,
                "documento_url": p.documento_url,
                "source_url": p.source_url,
                "source_id": p.source_id,
            }
            for p in pubs
        ]
    }

@app.get("/cases/id/{case_id}/publicaciones")
async def get_case_publications_by_id(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    return await get_case_publications(case.radicado, db)

@app.post("/cases/{radicado}/refresh-publicaciones")
async def refresh_publications(radicado: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.radicado == radicado).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    background_tasks.add_task(save_new_publications_task, case.id)
    return {"ok": True, "message": "Sincronizacin iniciada en segundo plano"}

@app.post("/cases/id/{case_id}/refresh-publicaciones")
async def refresh_publications_by_id(case_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    background_tasks.add_task(save_new_publications_task, case.id)
    return {"ok": True, "message": "Sincronizacin iniciada en segundo plano"}

async def save_new_publications_task(case_id: int):
    """Wrapper para ejecutar save_new_publications con su propia sesin de DB."""
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            await save_new_publications(case, db)
            db.commit()
    except Exception as e:
        print(f"[back-sync] Error en tarea de fondo: {e}")
    finally:
        db.close()

async def save_new_publications(case: Case, db: Session):
    try:
        from backend.service.publicaciones import is_relevant_actuacion, consultar_publicaciones_rango
        
        from backend.models import CaseEvent
        # 1. Obtener actuaciones del caso
        eventos = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).all()
        actuaciones = [{"anotacion": e.title, "fechaActuacion": e.event_date} for e in eventos]
        
        if not relevantes:
            print(f" No hay actuaciones con palabras clave 'auto', 'fijacion' o 'estado' para radicado {case.radicado}")
            return

        # 3. Limitar a las 5 ms recientes para evitar Timeouts (504)
        relevantes = relevantes[:5]
        print(f"[refresh] Iniciando bsqueda de publicaciones para {case.radicado} (Actuaciones a revisar: {len(relevantes)})")

        # 3. Para cada actuacin relevante, buscar en Publicaciones en su ventana de tiempo
        for act in relevantes:
            fecha_act_str = act.get("fechaActuacion") or ""
            if not fecha_act_str: continue
            
            try:
                results = await consultar_publicaciones_rango(
                    case.radicado, 
                    fecha_act_str, 
                    demandante=case.demandante or "",
                    demandado=case.demandado or ""
                )
                
                for p in results:
                    exists = db.query(CasePublication).filter(
                        CasePublication.case_id == case.id,
                        CasePublication.source_id == p["source_id"]
                    ).first()
                    
                    if not exists:
                        db.add(CasePublication(
                            case_id=case.id,
                            fecha_publicacion=parse_fecha_pub(p["fecha"]),
                            tipo_publicacion=p["tipo"],
                            descripcion=p["descripcion"],
                            documento_url=p["documento_url"],
                            source_url=p.get("source_url"),
                            source_id=p["source_id"]
                        ))
                    else:
                        exists.documento_url = p["documento_url"]
                try:
                    # Fix too many values to unpack (expected 2)
                    validation_result = await validar_radicado_completo(c.radicado, db)
                    if isinstance(validation_result, tuple):
                        res, msg = validation_result
                    else:
                        res, msg = validation_result, "Resultado de validacion unico"
                    
                    print(f"[pending-loop] Resultado para {c.radicado}: {res}")
                except Exception as loop_e:
                    print(f"[pending-loop] Error en {c.radicado}: {loop_e}")
            except Exception as e:
                print(f"[refresh] Error procesando ventana de publicacin para {case.radicado}: {e}")
                
    except Exception as e:
        print(f"[refresh] Error guardando publicaciones: {e}")

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
    
    class Config:
        extra = "ignore"


class ChecklistItemCreate(BaseModel):
    content: str

class CommentCreate(BaseModel):
    task_id: int
    content: str

@app.get("/projects/workspaces")
async def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna la jerarquia completa de espacios para el usuario."""
    if current_user.is_admin:
        workspaces = db.query(Workspace).all()
        
        # Solo para modo local: si no hay espacios, crear un flujo local m?nimo por defecto
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
        ).all()
    
    results = []
    for ws in workspaces:
        folders = []
        for f in ws.folders:
            lists = [{"id": l.id, "name": l.name} for l in f.lists]
            folders.append({"id": f.id, "name": f.name, "lists": lists})
        
        results.append({
            "id": ws.id,
            "name": ws.name,
            "visibility": ws.visibility,
            "clickup_id": ws.clickup_id,
            "folders": folders
        })
    
    return results

@app.post("/projects/workspaces")
async def create_workspace(
    ws_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ws = Workspace(name=ws_data.name, description=ws_data.description, visibility=ws_data.visibility, owner_id=current_user.id)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws

@app.post("/projects/folders")
async def create_folder(
    f_data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    f = Folder(name=f_data.name, workspace_id=f_data.workspace_id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f

@app.post("/projects/lists")
async def create_list(
    l_data: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    l = ProjectList(name=l_data.name, folder_id=l_data.folder_id, workspace_id=l_data.workspace_id)
    db.add(l)
    db.commit()
    db.refresh(l)
    return l

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
        joinedload(Task.subtasks),
        joinedload(Task.tags),
        joinedload(Task.attachments)
    )
    
    # Aplicar filtros adicionales
    if list_id:
        query = query.filter(Task.list_id == list_id)
    if case_id:
        query = query.filter(Task.case_id == case_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if status:
        query = query.filter(Task.status.ilike(f"%{status}%"))
        
    return query.order_by(desc(Task.created_at)).all()

@app.get("/api/tasks/{task_id}")
@app.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).options(
        joinedload(Task.checklists),
        joinedload(Task.subtasks),
        joinedload(Task.comments),
        joinedload(Task.tags),
        joinedload(Task.attachments)
    ).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Sincronización inteligente on-demand si es tarea de ClickUp
    if task.clickup_id:
        try:
            # Necesitamos el token de ClickUp del usuario (asumiendo que está en el ambiente o se pasa)
            # Para simplificar, intentamos buscar el token en la sesión del usuario o config
            # En este sistema el token se maneja en el frontend, así que lo ideal es recibirlo.
            # Pero como estamos en el backend, usaremos el token de la última sincronización si estuviera guardado.
            # MEJOR: Si el usuario es el dueño o admin, y tenemos acceso a su token (que el frontend envía en los headers)
            api_token = request.headers.get("X-ClickUp-Token") # Asumimos que el frontend lo enviará
            if api_token:
                from backend.clickup_sync import fetch_clickup, process_task
                # Traemos la tarea con subtareas y checklists en una sola llamada optimizada
                t_data = await fetch_clickup(f"task/{task.clickup_id}?include_subtasks=true&include_checklists=true", api_token)
                if t_data:
                    # Cache de usuarios para mapeo
                    all_users = db.query(User).all()
                    user_map = { (u.nombre or '').lower().strip(): u.id for u in all_users if u.nombre }
                    user_map.update({ (u.username or '').lower().strip(): u.id for u in all_users })
                    
                    await process_task(t_data, task.list_id, db, current_user.id, user_map, api_token, inherited_case_id=task.case_id)
                    db.commit()
                    db.refresh(task)
        except Exception as e:
            print(f"[OnDemand Sync Error] {e}")

    return task

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
    if lid is None:
        # Intentar buscar una lista por defecto o crear una
        default_list = db.query(ProjectList).filter(ProjectList.name == "BANDEJA DE ENTRADA").first()
        if not default_list:
            # Buscar la primera lista disponible
            default_list = db.query(ProjectList).first()
        
        if default_list:
            lid = default_list.id
            print(f" [TASK] Asignando lista por defecto ID {lid}")

    task = Task(
        title=t_data.title,
        description=t_data.description,
        list_id=lid,
        assignee_id=t_data.assignee_id,
        priority=t_data.priority,
        status=t_data.status,
        due_date=t_data.due_date,
        case_id=t_data.case_id,
        parent_id=t_data.parent_id,
        creator_id=current_user.id
    )
    db.add(task)
    if "assignee_name" in update_data:
        task.assignee_name = update_data["assignee_name"]
    
    db.commit()
    db.refresh(task)
    return task

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
        user_id=current_user.id
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
    
    if t_data.title is not None: task.title = t_data.title
    if t_data.description is not None: task.description = t_data.description
    if t_data.status is not None: task.status = t_data.status
    if t_data.assignee_id is not None: task.assignee_id = t_data.assignee_id
    if t_data.priority is not None: task.priority = t_data.priority
    if t_data.due_date is not None: task.due_date = t_data.due_date
    if t_data.assignee_name is not None: task.assignee_name = t_data.assignee_name
    if hasattr(t_data, 'case_id') and t_data.case_id is not None: task.case_id = t_data.case_id
    
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
    return task

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
    # month_actions: eventos filtrados manualmente si el formato String var?a
    first_of_month_str = hoy.replace(day=1).strftime("%Y-%m-%d")
    month_actions = db.query(CaseEvent).filter(CaseEvent.event_date >= first_of_month_str).count()
    
    # 2. Conteo de casos por Abogado (desglose)
    q_abogados = db.query(Case.abogado, func.count(Case.id)).filter(Case.abogado.isnot(None), Case.abogado != "")
    if not current_user.is_admin:
        q_abogados = q_abogados.filter(Case.user_id == current_user.id)
    lawyer_counts = q_abogados.group_by(Case.abogado).all()
    lawyer_stats = [{"name": l[0], "count": l[1]} for l in lawyer_counts]
    
    # 3. Alertas (casos sin leer) calculando la misma l?gica que en list_cases
    q_unread = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
        )
    )
    if not current_user.is_admin:
        q_unread = q_unread.filter(Case.user_id == current_user.id)
        
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

@app.get("/api/v1/system/health")
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
