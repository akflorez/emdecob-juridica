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
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, and_, case
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
from passlib.context import CryptContext
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from contextlib import asynccontextmanager

from .db import SessionLocal, engine, Base
from .models import Case, CaseEvent, NotificationConfig, NotificationLog, InvalidRadicado, User
from .service.rama import (
    consulta_por_radicado,
    detalle_proceso,
    actuaciones_proceso,
    documentos_actuacion,
    RamaError,
)


# =========================
# ZONA HORARIA COLOMBIA
# =========================
TIMEZONE_CO = pytz.timezone("America/Bogota")

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
                print(f"📧 [flush-loop] Son las {NOTIFICATION_FLUSH_HOUR}:00 — enviando {len(_notification_accumulator)} casos acumulados")
                send_grouped_notification(list(_notification_accumulator))
                _notification_accumulator.clear()
                _already_flushed_today = hoy
        except Exception as e:
            print(f"⚠️ [flush-loop] Error: {e}")


# =========================
# AUTO-REFRESH EN BACKGROUND
# =========================
async def auto_refresh_loop():
    global auto_refresh_running, auto_refresh_stats

    print("⏳ Esperando 60 segundos antes del primer auto-refresh...")
    await asyncio.sleep(60)

    print(f"⏰ Auto-refresh continuo iniciado — revisará TODOS los casos en cada ciclo")

    while auto_refresh_running:
        try:
            now = now_colombia()
            print(f"\n🔄 [{now.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando ciclo completo de auto-refresh...")
            auto_refresh_stats["last_run"] = now.isoformat()
            auto_refresh_stats["next_run"] = "Al terminar este ciclo + 10 min"

            result = await do_auto_refresh()

            auto_refresh_stats["last_result"] = result
            print(f"✅ Ciclo completo: {result.get('checked', 0)} revisados, {result.get('updated_cases', 0)} con cambios")

            hora = now_colombia().hour
            if hora >= NOTIFICATION_FLUSH_HOUR and _notification_accumulator:
                print(f"📧 Flush de 5 PM: enviando {len(_notification_accumulator)} casos acumulados")
                send_grouped_notification(_notification_accumulator)
                _notification_accumulator.clear()

            auto_refresh_stats["next_run"] = "En 10 minutos"
            await asyncio.sleep(600)

        except Exception as e:
            print(f"💥 Error en auto-refresh: {e}")
            auto_refresh_stats["last_result"] = {"error": str(e)}
            await asyncio.sleep(300)


async def do_auto_refresh() -> dict:
    from sqlalchemy import text

    BATCH_SIZE = 5
    MINI_BATCH = 10
    DELAY_BETWEEN = 1.0
    EXTRA_EVERY_N = 10
    EXTRA_DELAY   = 1.0

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

        print(f"📊 Verificando {len(case_ids)} de {total_cases} casos...")

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
                    print(f"   🔗 Conexión renovada en caso {i+1}/{len(case_ids)}")

                c = db.query(Case).filter(Case.id == case_id).first()
                if not c:
                    continue

                try:
                    resp = await consulta_por_radicado(c.radicado, solo_activos=False, pagina=1)
                    items = extract_items(resp)
                except RamaError as e:
                    print(f"   ⚠️ Error consultando {c.radicado}: {e}")
                    errors += 1
                    if "bloqueó" in str(e).lower() or "rate" in str(e).lower():
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

                if hay_cambio and es_actuacion_reciente:
                    sujetos = p.get("sujetosProcesales") or ""
                    d1, d2  = parse_sujetos_procesales(sujetos)
                    c.demandante     = d1 or c.demandante
                    c.demandado      = d2 or c.demandado
                    c.ultima_actuacion = nueva_fecha
                    new_hash = sha256_obj({"radicado": c.radicado, "ultima_actuacion": str(nueva_fecha), "ts": now_colombia().isoformat()})
                    c.current_hash   = new_hash
                    updated_cases.append({
                        "radicado": c.radicado,
                        "demandante": c.demandante,
                        "demandado": c.demandado,
                        "juzgado": c.juzgado,
                        "ultima_actuacion": nueva_fecha.isoformat() if nueva_fecha else None,
                        "fecha_anterior":   fecha_actual.isoformat() if fecha_actual else None,
                    })
                elif hay_cambio and not es_actuacion_reciente:
                    c.ultima_actuacion = nueva_fecha
                    new_hash = sha256_obj({"radicado": c.radicado, "ultima_actuacion": str(nueva_fecha), "ts": now_colombia().isoformat()})
                    c.current_hash = new_hash
                    c.last_hash    = new_hash

                sujetos_raw = p.get("sujetosProcesales") or ""
                if sujetos_raw:
                    d1f, d2f = parse_sujetos_procesales(sujetos_raw)
                    if d1f: c.demandante = d1f
                    if d2f: c.demandado  = d2f

                c.last_check_at = now_colombia()
                checked += 1

                if (i + 1) % MINI_BATCH == 0:
                    try:
                        db.commit()
                        print(f"   💾 Commit parcial: {i+1}/{len(case_ids)} casos")
                    except Exception as e:
                        print(f"   ⚠️ Error en commit parcial: {e} — reconectando...")
                        try: db.rollback()
                        except: pass
                        try: db.close()
                        except: pass
                        db = get_fresh_db()

            except Exception as e:
                print(f"   💥 Error procesando caso_id={case_id}: {e}")
                errors += 1
                if "ssl" in str(e).lower() or "connection" in str(e).lower():
                    try:
                        if db: db.close()
                    except: pass
                    db = get_fresh_db()

        if db:
            try:
                db.commit()
                print(f"   💾 Commit final")
            except Exception as e:
                print(f"   ⚠️ Error en commit final: {e}")
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
        print(f"💥 Error en do_auto_refresh: {e}")
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
        print(f"   ⚠️ Error guardando actuaciones: {e}")


def _accumulate_and_notify(new_cases: List[dict]):
    global _notification_accumulator, _notification_accumulator_date

    hoy = today_colombia()

    if _notification_accumulator_date and _notification_accumulator_date < hoy:
        print(f"📧 Acumulador de {_notification_accumulator_date} descartado — nuevo día")
        _notification_accumulator = []

    _notification_accumulator_date = hoy

    radicados_existentes = {c["radicado"] for c in _notification_accumulator}
    for c in new_cases:
        if c["radicado"] not in radicados_existentes:
            _notification_accumulator.append(c)
            radicados_existentes.add(c["radicado"])

    total = len(_notification_accumulator)
    hora  = now_colombia().hour

    print(f"📧 Acumulador: {total} casos | hora={hora}:00")

    should_send = (
        total >= NOTIFICATION_BATCH_SIZE
        or (hora >= NOTIFICATION_FLUSH_HOUR and total > 0)
    )

    if should_send:
        print(f"📧 Enviando correo con {total} casos acumulados...")
        send_grouped_notification(_notification_accumulator)
        _notification_accumulator = []
    else:
        print(f"📧 Acumulando... {total}/{NOTIFICATION_BATCH_SIZE} casos (envío a las {NOTIFICATION_FLUSH_HOUR}:00 si no se llega antes)")


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
        subject = f"🔔 {count} caso{'s' if count > 1 else ''} con nuevas actuaciones - EMDECOB"

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
                  <td style="padding:8px;border:1px solid #ddd;font-family:monospace;font-size:12px;">{case.get('radicado', '—')}</td>
                  <td style="padding:8px;border:1px solid #ddd;">{case.get('demandante', '—') or '—'}</td>
                  <td style="padding:8px;border:1px solid #ddd;">{case.get('demandado', '—') or '—'}</td>
                  <td style="padding:8px;border:1px solid #ddd;font-size:12px;">{case.get('juzgado', '—') or '—'}</td>
                  <td style="padding:8px;border:1px solid #ddd;text-align:center;">{case.get('ultima_actuacion', '—') or '—'}</td>
                </tr>
                """

            body = f"""
            <html>
            <body style="font-family:Arial,sans-serif;padding:20px;">
              <h2 style="color:#0d9488;">🔔 Nuevas Actuaciones Detectadas</h2>
              <p>Se han detectado <strong>{count}</strong> caso{'s' if count > 1 else ''} con nuevas actuaciones:</p>

              <table style="border-collapse:collapse;width:100%;margin-top:20px;">
                <thead>
                  <tr style="background:#0d9488;color:white;">
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Radicado</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Demandante</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Demandado</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Juzgado</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:center;">Últ. Actuación</th>
                  </tr>
                </thead>
                <tbody>
                  {rows_html}
                </tbody>
              </table>
              <hr style="margin-top:30px;">
              <p style="color:#888;font-size:12px;">
                Mensaje automático EMDECOB Consultas<br>
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
    ).order_by(desc(Case.ultima_actuacion)).all()

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

    print("🔄 [pending-loop] Loop de validación de pendientes activo")
    await asyncio.sleep(15)

    while True:
        db = None
        try:
            db = SessionLocal()
            total = db.query(Case).filter(Case.juzgado.is_(None)).count()

            if total > 0:
                print(f"🔄 [pending-loop] {total} casos pendientes — validando lote de {min(BATCH, total)}...")
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
                            print(f"   ✅ [pending-loop] Validado: {c.radicado}")
                        else:
                            inv = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == c.radicado).first()
                            if inv:
                                inv.intentos += 1
                                inv.updated_at = now_colombia()
                            else:
                                db.add(InvalidRadicado(radicado=c.radicado, motivo="No encontrado en Rama Judicial", intentos=1))
                            print(f"   ⚠️ [pending-loop] No encontrado (reintentará): {c.radicado}")
                        db.flush()
                    except Exception as e:
                        print(f"   💥 [pending-loop] Error en {c.radicado}: {e}")

                db.commit()
                remaining = db.query(Case).filter(Case.juzgado.is_(None)).count()
                print(f"🔄 [pending-loop] Ciclo completo. Restantes: {remaining}")
            else:
                print("🔄 [pending-loop] Sin pendientes. Próxima revisión en 5 min.")

        except Exception as e:
            print(f"💥 [pending-loop] Error en ciclo: {e}")
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

    print("🚀 Iniciando EMDECOB Consultas...")
    Base.metadata.create_all(bind=engine)
    _ensure_default_user()
    asyncio.create_task(notification_flush_loop())
    print("📧 Flush loop de notificaciones iniciado")

    auto_refresh_running = True
    auto_refresh_stats["running"] = True
    auto_refresh_task = asyncio.create_task(auto_refresh_loop())
    print(f"⏰ Auto-refresh iniciado (cada {auto_refresh_stats['interval_minutes']} minutos)")

    asyncio.create_task(_pending_validation_loop())
    print("🔄 Validación continua de pendientes iniciada")

    yield

    print("🛑 Deteniendo EMDECOB Consultas...")
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
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "https://emdecob-juridica.vercel.app",
        "http://consultasjuridicas.emdecob.co",
        "https://consultasjuridicas.emdecob.co",
    ],
    allow_credentials=True,
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
# AUTH — Stateless Tokens
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
    except Exception:
        return None

bearer_scheme = HTTPBearer(auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        "id": 9998,
        "nombre": "FNA Jurídica",
        "is_admin": False,
    },
}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(lambda: next(iter([SessionLocal()]))),
) -> "User":
    if not credentials:
        raise HTTPException(status_code=401, detail="No autenticado")
    token = credentials.credentials
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Fake users para hardcoded fallback
    if user_id == 9999:
        return User(id=9999, username="admin", nombre="Administrador", is_admin=True, is_active=True)
    if user_id == 9998:
        return User(id=9998, username="fna_juridica", nombre="FNA Jurídica", is_admin=False, is_active=True)

    db_local = SessionLocal()
    try:
        user = db_local.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
        return user
    finally:
        db_local.close()


def _ensure_default_user():
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.username == "fna_juridica").first()
        if not exists:
            db.add(User(
                username="fna_juridica",
                hashed_password=_hash_password("juridicaEmdecob2026$"),
                nombre="FNA Jurídica",
                is_active=True,
                is_admin=False,
            ))
            db.commit()
            print("✅ Usuario fna_juridica creado automáticamente")
        else:
            print("👤 Usuario fna_juridica ya existe")
    except Exception as e:
        print(f"⚠️ Error creando usuario por defecto: {e}")
    finally:
        db.close()


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

_FNA_KEYWORDS = {"FONDO NACIONAL DEL AHORRO", "FNA", "FONDO NAL DEL AHORRO", "F.N.A."}

def _es_fna(nombre: str) -> bool:
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
        return None, None

    demandante = None
    demandado = None

    if isinstance(sujetos, list):
        ROLES_DEMANDANTE = {"demandante", "accionante", "demandante/accionante", "accionante/demandante", "ejecutante"}
        ROLES_DEMANDADO  = {"demandado", "accionado", "demandado/accionado", "ejecutado", "deudor"}
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
        demandante, demandado = _asignar_roles_inteligente(demandante, demandado)
        return demandante, demandado

    if not isinstance(sujetos, str):
        try:
            sujetos = str(sujetos)
        except Exception:
            return None, None

    dem_match = re.search(
        r"(?:Demandante(?:[/\-]\w+)?|Accionante|Ejecutante)\s*:\s*([^|]+)",
        sujetos, re.IGNORECASE
    )
    if dem_match:
        demandante = _normalizar_nombre(dem_match.group(1))

    ddo_match = re.search(
        r"(?:Demandado(?:[/\-]\w+)?|Accionado|Ejecutado|Deudor)\s*:\s*([^|]+)",
        sujetos, re.IGNORECASE
    )
    if ddo_match:
        demandado = _normalizar_nombre(ddo_match.group(1))

    demandante, demandado = _asignar_roles_inteligente(demandante, demandado)
    return demandante, demandado

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
    fecha_proceso = (
        p.get("fechaProceso")
        or p.get("FechaProceso")
        or p.get("fechaRadicacion")
        or p.get("FechaRadicacion")
        or p.get("fechaProcesoRadicacion")
    )
    fecha_ult = (
        p.get("fechaUltimaActuacion")
        or p.get("FechaUltimaActuacion")
        or p.get("ultimaActuacion")
        or p.get("UltimaActuacion")
    )

    if det and isinstance(det, dict):
        if not fecha_proceso:
            fecha_proceso = (
                det.get("fechaRadicacion")
                or det.get("fechaProceso")
                or det.get("FechaProceso")
                or det.get("FechaRadicacion")
            )
        if not fecha_ult:
            fecha_ult = (
                det.get("fechaUltimaActuacion")
                or det.get("FechaUltimaActuacion")
                or det.get("ultimaActuacion")
            )

    return fecha_proceso, fecha_ult

def extract_juzgado(p: dict, det: Optional[dict]) -> Optional[str]:
    juzgado = (
        p.get("despacho")
        or p.get("Despacho")
        or p.get("nombreDespacho")
        or p.get("NombreDespacho")
        or p.get("juzgado")
        or p.get("Juzgado")
    )

    if not juzgado and det and isinstance(det, dict):
        juzgado = (
            det.get("despacho")
            or det.get("Despacho")
            or det.get("nombreDespacho")
            or det.get("NombreDespacho")
            or det.get("juzgado")
            or det.get("Juzgado")
        )

    return juzgado

async def obtener_id_proceso(radicado: str) -> Optional[int]:
    resp = await consulta_por_radicado(radicado, solo_activos=False, pagina=1)
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
            print(f"   🌐 [fallback] GET {url}")

            try:
                resp = await client.get(url)
                print(f"   🌐 [fallback] status={resp.status_code} | body={resp.text[:400]}")

                if resp.status_code in (404, 403, 429):
                    continue
                if resp.status_code != 200:
                    continue

                try:
                    data = resp.json()
                except Exception as e:
                    print(f"   🌐 [fallback] Error JSON en {path}: {e}")
                    continue

                docs = extract_documentos_from_response(data)
                if docs:
                    print(f"   🌐 [fallback] ✅ {len(docs)} docs en: {path}")
                    return docs

            except Exception as e:
                print(f"   🌐 [fallback] Error en {path}: {e}")

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
    d1, d2 = parse_sujetos_procesales(sujetos)
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
        try:
            await delay_between_requests(0.1, 0.3)
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
                    if con_docs:
                        c.has_documents = True
        except Exception as e:
            print(f"   ⚠️ Error actuaciones: {e}")

    return {"found": True, "case": c}


# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"status": "ok", "app": "EMDECOB Consultas"}


# =========================
# STATS
# =========================
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_validos = db.query(Case).filter(Case.juzgado.isnot(None)).count()
    total_invalidos = db.query(InvalidRadicado).count()
    total_pendientes = db.query(Case).filter(Case.juzgado.is_(None)).count()

    hoy = today_colombia()
    ayer = hoy - timedelta(days=1)

    total_no_leidos = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
        )
    ).count()

    total_actualizados_hoy = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.ultima_actuacion == hoy,
    ).count()

    return {
        "total_validos": total_validos,
        "total_invalidos": total_invalidos,
        "total_pendientes": total_pendientes,
        "total_no_leidos": total_no_leidos,
        "total_actualizados_hoy": total_actualizados_hoy,
    }


# =========================
# AUTH — LOGIN / LOGOUT / USUARIOS
# =========================

@app.post("/auth/login")
def login(data: LoginRequest):
    """Autentica un usuario y retorna un token de sesión."""

    # ── Primero intentar contra la base de datos ──
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.username == data.username,
            User.is_active == True
        ).first()

        if user and _verify_password(data.password, user.hashed_password):
            token = create_access_token(user.id)
            return {
                "token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "nombre": user.nombre,
                    "is_admin": user.is_admin,
                }
            }
    except Exception as e:
        print(f"⚠️ [login] Error consultando BD: {e} — usando fallback")
    finally:
        db.close()

    # ── Fallback hardcodeado (funciona aunque la BD falle) ──
    hc = HARDCODED_USERS.get(data.username)
    if hc and data.password == hc["password"]:
        token = create_access_token(hc["id"])
        return {
            "token": token,
            "token_type": "bearer",
            "user": {
                "id": hc["id"],
                "username": data.username,
                "nombre": hc["nombre"],
                "is_admin": hc["is_admin"],
            }
        }

    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


@app.post("/auth/logout")
def logout():
    return {"ok": True, "message": "Sesión cerrada"}


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
    if not current_user.is_admin:
        raise HTTPException(403, "Solo administradores pueden ver los usuarios")
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
        raise HTTPException(400, "El intervalo mínimo es 5 minutos")
    if data.interval_minutes > 1440:
        raise HTTPException(400, "El intervalo máximo es 1440 minutos (24 horas)")
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
            pendientes = db.query(Case).filter(Case.juzgado.is_(None)).limit(5).all()
            for i, c in enumerate(pendientes):
                try:
                    if i > 0:
                        await asyncio.sleep(1.0)
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
                    print(f"⚠️ [cron-pending] Error en {c.radicado}: {e}")
            db.commit()
            db.close()
        except Exception as e:
            print(f"⚠️ [cron-pending] Error general: {e}")

        # 3. Reintentar no encontrados
        invalid_result = {"found": 0, "still_not_found": 0}
        try:
            db = SessionLocal()
            invalidos = db.query(InvalidRadicado).order_by(InvalidRadicado.updated_at.asc()).limit(5).all()
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
                    print(f"⚠️ [cron-invalid] Error en {item.radicado}: {e}")
            db.commit()
            db.close()
        except Exception as e:
            print(f"⚠️ [cron-invalid] Error general: {e}")

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
def get_notification_config(db: Session = Depends(get_db)):
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
def update_notification_config(data: NotificationConfigUpdate, db: Session = Depends(get_db)):
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
    return {"ok": True, "message": "Configuración guardada"}

@app.post("/config/notifications/test")
def test_notification_email(data: TestEmailRequest, db: Session = Depends(get_db)):
    config = db.query(NotificationConfig).first()
    if not config:
        raise HTTPException(400, "No hay configuración guardada")
    if not config.smtp_user or not config.smtp_pass:
        raise HTTPException(400, "Falta configurar usuario y contraseña SMTP")

    try:
        body = f"""
        <html><body style="font-family:Arial;padding:20px;">
        <h2 style="color:#0d9488;">✅ Prueba de Notificación</h2>
        <p>Si recibiste este correo, la configuración SMTP está correcta.</p>
        <p style="color:#888;font-size:12px;">Fecha: {now_colombia().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body></html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "✅ Prueba SMTP - EMDECOB Consultas"
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
            return {"ok": True, "sent": False, "message": "No hay casos no leídos para enviar", "count": 0}

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
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
):
    q = db.query(InvalidRadicado)
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
def download_invalid_radicados_excel(db: Session = Depends(get_db)):
    items = db.query(InvalidRadicado).order_by(desc(InvalidRadicado.updated_at)).all()

    data = [
        {
            "Radicado": x.radicado,
            "Motivo": x.motivo,
            "Intentos": x.intentos,
            "Fecha Registro": x.created_at.strftime("%Y-%m-%d %H:%M") if x.created_at else "",
            "Último Intento": x.updated_at.strftime("%Y-%m-%d %H:%M") if x.updated_at else "",
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
# CASES LIST
# =========================
@app.get("/cases")
def list_cases(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(default=None),
    juzgado: Optional[str] = Query(default=None),
    mes_actuacion: Optional[str] = Query(default=None),
    solo_validos: bool = Query(default=True),
    solo_pendientes: bool = Query(default=False),
    solo_no_leidos: bool = Query(default=False),
    solo_actualizados_hoy: bool = Query(default=False),
    con_documentos: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=2000),
):
    q = db.query(Case)

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

    unread_count = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer_count),
        )
    ).count()

    unread_order = case(
        (and_(Case.current_hash.isnot(None), Case.last_hash.isnot(None), Case.current_hash != Case.last_hash), 0),
        (and_(Case.current_hash.isnot(None), Case.last_hash.is_(None), Case.ultima_actuacion >= ayer_count), 0),
        else_=1
    )

    items = (
        q.order_by(unread_order, desc(Case.ultima_actuacion), desc(Case.updated_at))
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
    search: Optional[str] = Query(default=None),
    juzgado: Optional[str] = Query(default=None),
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

    cases = q.order_by(desc(Case.ultima_actuacion)).all()

    data = [
        {
            "Radicado": c.radicado,
            "Demandante": c.demandante or "",
            "Demandado": c.demandado or "",
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
async def validate_batch(db: Session = Depends(get_db), batch_size: int = Query(default=50, ge=1, le=200)):
    pendientes = db.query(Case).filter(Case.juzgado.is_(None)).limit(batch_size).all()

    if not pendientes:
        return {"ok": True, "processed": 0, "validated": 0, "not_found": 0, "remaining": 0, "message": "No hay más casos pendientes"}

    validated = 0
    not_found = 0

    for i, c in enumerate(pendientes):
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
            db.flush()
        except Exception:
            pass

    db.commit()
    remaining = db.query(Case).filter(Case.juzgado.is_(None)).count()

    return {
        "ok": True, "processed": len(pendientes), "validated": validated, "not_found": not_found,
        "remaining": remaining, "message": f"Procesados {len(pendientes)}: {validated} validados, {not_found} no encontrados."
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

        p = items[0] or {}
        id_proceso = p.get("idProceso") or p.get("IdProceso")

        det = {}
        if id_proceso:
            try:
                det = await detalle_proceso(int(id_proceso))
            except:
                det = {}

        c = db.query(Case).filter(Case.radicado == r).first()
        is_new_case = False
        if not c:
            c = Case(radicado=r)
            db.add(c)
            db.flush()
            is_new_case = True

        sujetos = p.get("sujetosProcesales") or ""
        d1, d2 = parse_sujetos_procesales(sujetos)

        c.demandante = d1 or c.demandante
        c.demandado = d2 or c.demandado
        c.juzgado = extract_juzgado(p, det) or c.juzgado

        fecha_proceso_str, fecha_ult_str = extract_fecha_proceso(p, det)
        c.fecha_radicacion = parse_fecha(fecha_proceso_str) or c.fecha_radicacion
        c.ultima_actuacion = parse_fecha(fecha_ult_str) or c.ultima_actuacion

        if is_new_case:
            new_hash = sha256_obj({"proceso": p, "detalle": det})
            c.current_hash = new_hash
            c.last_hash = new_hash

        c.last_check_at = now_colombia()
        db.commit()

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
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")


# =========================
# EVENTS BY RADICADO
# =========================
@app.get("/cases/by-radicado/{radicado}/events")
async def get_events_by_radicado(radicado: str, db: Session = Depends(get_db)):
    try:
        r = clean_str(radicado)
        if not r:
            raise HTTPException(400, "Radicado requerido")

        c = db.query(Case).filter(Case.radicado == r).first()
        if not c:
            c = Case(radicado=r)
            db.add(c)
            db.flush()
            db.commit()

        try:
            id_proceso = await obtener_id_proceso(r)
        except RamaError as e:
            raise HTTPException(502, f"Error Rama Judicial: {str(e)}")

        if not id_proceso:
            return {"items": [], "total": 0}

        try:
            acts_resp = await actuaciones_proceso(int(id_proceso))
        except RamaError as e:
            raise HTTPException(502, f"Error obteniendo actuaciones: {str(e)}")

        acts = []
        if isinstance(acts_resp, dict):
            acts = acts_resp.get("actuaciones") or acts_resp.get("items") or []
        elif isinstance(acts_resp, list):
            acts = acts_resp

        result_items = []
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
            result_items.append(it)

        for it in result_items:
            event_hash = sha256_obj(it)
            exists = db.query(CaseEvent).filter(CaseEvent.case_id == c.id, CaseEvent.event_hash == event_hash).first()
            if not exists:
                con_docs = it.get("con_documentos", False)
                db.add(CaseEvent(
                    case_id=c.id,
                    event_date=it.get("event_date"),
                    title=it.get("title"),
                    detail=it.get("detail"),
                    event_hash=event_hash,
                    con_documentos=con_docs,
                ))
                if con_docs:
                    c.has_documents = True
        db.commit()

        return {"items": result_items, "total": len(result_items)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")


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
        raise HTTPException(404, "No se encontró el proceso")

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

    print("🔄 [bg-validate] Iniciando validación automática de pendientes...")
    for cycle in range(MAX_CYCLES):
        db = None
        try:
            db = SessionLocal()
            pendientes = db.query(Case).filter(Case.juzgado.is_(None)).limit(BATCH).all()
            if not pendientes:
                print("✅ [bg-validate] Sin pendientes. Fin.")
                break

            print(f"🔄 [bg-validate] Ciclo {cycle+1}: {len(pendientes)} casos...")
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
                    print(f"   ⚠️ [bg-validate] Error en {c.radicado}: {e}")
            db.commit()

            remaining = db.query(Case).filter(Case.juzgado.is_(None)).count()
            print(f"🔄 [bg-validate] Restantes: {remaining}")
            if remaining == 0:
                break

            await asyncio.sleep(5)

        except Exception as e:
            print(f"💥 [bg-validate] Error ciclo {cycle+1}: {e}")
        finally:
            if db:
                db.close()

    print("✅ [bg-validate] Validación automática finalizada.")


# =========================
# IMPORT EXCEL
# =========================
@app.post("/cases/import-excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
        rad_col = next((c for c in ["Radicado", "radicado", "RADICADO"] if c in df.columns), None)
        if not rad_col:
            raise HTTPException(400, "Falta la columna 'Radicado'")

        created = 0
        skipped = 0

        for _, row in df.iterrows():
            radicado = clean_str(row.get(rad_col))
            if not radicado:
                skipped += 1
                continue

            existing_case = db.query(Case).filter(Case.radicado == radicado).first()
            if existing_case:
                skipped += 1
                continue

            existing_invalid = db.query(InvalidRadicado).filter(InvalidRadicado.radicado == radicado).first()
            if existing_invalid:
                skipped += 1
                continue

            db.add(Case(radicado=radicado))
            created += 1

        db.commit()

        if created > 0:
            asyncio.create_task(_background_validate_pendientes())

        return {
            "ok": True,
            "created": created,
            "skipped": skipped,
            "invalid_count": 0,
            "message": f"Importados {created} radicados. Validación automática iniciada en segundo plano."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")


# =========================
# REFRESH ALL (MANUAL)
# =========================
@app.post("/cases/refresh-all")
async def refresh_all_cases():
    try:
        result = await do_auto_refresh()
        return result
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")


# =========================
# DOCUMENTOS DE ACTUACIÓN
# =========================
@app.get("/cases/events/{id_reg_actuacion}/documents")
async def get_event_documents(
    id_reg_actuacion: int,
    llave_proceso: str = Query(..., description="La llave (radicado) del proceso de 23 dígitos")
):
    print(f"\n📄 [DOCS] id_reg_actuacion={id_reg_actuacion} | llave_proceso={llave_proceso}")

    items = []

    try:
        raw = await documentos_actuacion(id_reg_actuacion, llave_proceso)
        print(f"📄 [DOCS] service/rama.documentos_actuacion() → tipo={type(raw).__name__} | valor={str(raw)[:300]}")
        items = extract_documentos_from_response(raw)
        print(f"📄 [DOCS] items extraídos del servicio: {len(items)}")
    except RamaError as e:
        print(f"📄 [DOCS] RamaError en servicio: {e}")
    except Exception as e:
        print(f"📄 [DOCS] Error en servicio: {e}")
        traceback.print_exc()

    if not items:
        print(f"📄 [DOCS] Servicio retornó vacío. Intentando llamada directa a Rama Judicial...")
        try:
            items = await fetch_documentos_rama_directa(id_reg_actuacion, llave_proceso)
            print(f"📄 [DOCS] items desde llamada directa: {len(items)}")
        except Exception as e:
            print(f"📄 [DOCS] Error en llamada directa: {e}")
            traceback.print_exc()

    print(f"📄 [DOCS] Resultado final → {len(items)} documentos")
    return {"items": items, "total": len(items)}


# =========================
# DESCARGA DE DOCUMENTO (PROXY A RAMA JUDICIAL)
# =========================
@app.get("/documentos/{id_documento}/descargar")
async def descargar_documento_endpoint(id_documento: int):
    url_rama = f"{RAMA_BASE}/Descarga/Documento/{id_documento}"
    print(f"📥 Descargando documento ID={id_documento} → {url_rama}")

    try:
        client = httpx.AsyncClient(timeout=60.0, verify=False, headers=RAMA_HEADERS)
        response = await client.send(
            client.build_request("GET", url_rama),
            stream=True
        )

        print(f"📥 Status Rama Judicial: {response.status_code}")

        if response.status_code != 200:
            await response.aclose()
            await client.aclose()
            raise HTTPException(
                status_code=response.status_code,
                detail=f"La Rama Judicial devolvió {response.status_code} para el documento {id_documento}."
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
        raise HTTPException(504, f"Timeout: La Rama Judicial tardó demasiado (documento {id_documento}).")
    except httpx.ConnectError as e:
        raise HTTPException(502, f"No se pudo conectar a la Rama Judicial: {str(e)}")
    except Exception as e:
        print(f"📥 Error inesperado descargando {id_documento}: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Error interno descargando documento: {str(e)}")