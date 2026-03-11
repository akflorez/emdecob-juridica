from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Text,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from .db import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String(60), unique=True, index=True, nullable=False)

    demandante = Column(String(255), nullable=True)
    demandado = Column(String(255), nullable=True)
    juzgado = Column(String(255), nullable=True)
    alias = Column(String(200), nullable=True)

    last_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=True)
    last_check_at = Column(DateTime, nullable=True)

    fecha_radicacion = Column(Date, nullable=True)
    ultima_actuacion = Column(Date, nullable=True)

    has_documents = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    event_date = Column(String(60), nullable=True)
    title = Column(String(255), nullable=True)
    detail = Column(Text, nullable=True)
    event_hash = Column(String(64), nullable=False)

    con_documentos = Column(Boolean, default=False)

    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id", "event_hash", name="uq_case_event"),
    )


class InvalidRadicado(Base):
    """Radicados que no se encontraron en Rama Judicial"""
    __tablename__ = "invalid_radicados"

    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String(60), unique=True, index=True, nullable=False)
    motivo = Column(String(255), default="No encontrado en Rama Judicial")
    intentos = Column(Integer, default=1)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class NotificationConfig(Base):
    """Configuración de notificaciones por correo"""
    __tablename__ = "notification_config"

    id = Column(Integer, primary_key=True, index=True)

    smtp_host = Column(String(255), default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=True)
    smtp_pass = Column(String(255), nullable=True)
    smtp_from = Column(String(255), nullable=True)

    notification_emails = Column(Text, nullable=True)

    is_active = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class NotificationLog(Base):
    """Historial de notificaciones enviadas"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)

    sent_at = Column(DateTime, server_default=func.now(), nullable=False)
    recipients = Column(Text, nullable=True)
    subject = Column(String(500), nullable=True)
    cases_count = Column(Integer, default=0)
    status = Column(String(50), default="sent")
    error_message = Column(Text, nullable=True)


class User(Base):
    """Usuarios del sistema"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=True)       # nombre visible
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )