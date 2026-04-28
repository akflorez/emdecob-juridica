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
    Table,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String(60), index=True, nullable=False)
    id_proceso = Column(String(20), unique=True, index=True, nullable=True) # ID único de Rama Judicial

    demandante = Column(String(255), nullable=True)
    demandado = Column(String(255), nullable=True)
    juzgado = Column(String(255), nullable=True)
    alias = Column(String(200), nullable=True)
    cedula = Column(String(50), nullable=True)
    abogado = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True) # Para mensajería Cally
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

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
    
    tasks = relationship("Task", back_populates="case", cascade="all, delete-orphan")


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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

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
    email = Column(String(255), unique=True, index=True, nullable=True) # Permitir nulo inicialmente para migracion
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=True)       # nombre visible
    telefono = Column(String(50), nullable=True)     # contacto para reportes
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CasePublication(Base):
    """Publicaciones procesales (Estados/Edictos) del portal nuevo"""
    __tablename__ = "case_publications"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    fecha_publicacion = Column(Date, nullable=True)
    tipo_publicacion = Column(String(255), nullable=True)
    descripcion = Column(Text, nullable=True)
    documento_url = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)     # URL original del portal
    source_id = Column(String(255), unique=True, index=True, nullable=True) # ID único del portal

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class SearchJob(Base):
    """Trabajos de búsqueda masiva (nombres o radicados)"""
    __tablename__ = "search_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False) # 'name', 'radicado'
    status = Column(String(50), default="pending") # 'pending', 'processing', 'completed', 'failed'
    
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    is_imported = Column(Boolean, default=False)
    
    # Almacena los resultados encontrados (radicados, etc) antes de importar
    results_json = Column(Text, nullable=True) 
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# =========================
# GESTOR DE PROYECTOS (ESTILO CLICKUP)
# =========================

class Workspace(Base):
    """Ambientes principales de trabajo (Ej: Civil, Laboral, FNA)"""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    visibility = Column(String(50), default="TEAM_COLLABORATION")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Referencia a ClickUp para sincronización
    clickup_id = Column(String(100), unique=True, index=True, nullable=True)
    
    folders = relationship("Folder", back_populates="workspace", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class WorkspaceMember(Base):
    """Miembros de un ambiente y sus permisos"""
    __tablename__ = "workspace_members"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # ADMIN, EDITOR, VIEWER
    role = Column(String(50), default="VIEWER")
    
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )


class Folder(Base):
    """Carpetas dentro de un Ambiente"""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    # Referencia a ClickUp para sincronización
    clickup_id = Column(String(100), unique=True, index=True, nullable=True)

    workspace = relationship("Workspace", back_populates="folders")
    lists = relationship("ProjectList", back_populates="folder", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ProjectList(Base):
    """Listas de tareas (Ej: Pendientes, Revisión, Finalizados)"""
    __tablename__ = "project_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    # Referencia a ClickUp para sincronización
    clickup_id = Column(String(100), unique=True, index=True, nullable=True)

    folder = relationship("Folder", back_populates="lists")
    tasks = relationship("Task", back_populates="project_list", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# =========================
# ASOCIACIONES DE ETIQUETAS
# =========================
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class Tag(Base):
    """Etiquetas personalizadas para clasificación en proyectos."""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    color = Column(String(50), default="#3b82f6") # Hex code
    
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")


class Task(Base):
    """Tareas individuales con jerarquía (soporta subtareas)"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # To do, In Progress, Done, etc.
    status = Column(String(50), default="To Do")
    priority = Column(String(50), nullable=True) # Low, Normal, High, Urgent
    
    due_date = Column(DateTime, nullable=True)
    
    list_id = Column(Integer, ForeignKey("project_lists.id", ondelete="CASCADE"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Vinculación clave con los expedientes/casos jurídicos
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Soporte para subtareas (recursivo)
    parent_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    
    # Referencia a ClickUp para evitar duplicados en importación
    clickup_id = Column(String(100), unique=True, index=True, nullable=True)
    
    project_list = relationship("ProjectList", back_populates="tasks")
    case = relationship("Case", back_populates="tasks")
    
    # Colecciones de checklist y tags
    checklists = relationship("TaskChecklistItem", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class TaskComment(Base):
    """Comentarios en las tareas"""
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class TaskChecklistItem(Base):
    """Sub-elementos tipo checklist rápidos dentro de una tarea"""
    __tablename__ = "task_checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(500), nullable=False)
    is_completed = Column(Boolean, default=False)
    
    task = relationship("Task", back_populates="checklists")
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class TaskAttachment(Base):
    """Archivos o imágenes adjuntas a una tarea"""
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class IntegrationConfig(Base):
    """Configuración de integraciones externas (Cally, etc)"""
    __tablename__ = "integration_config"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), unique=True, index=True, nullable=False)
    api_key = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(Text, nullable=True) # JSON flexible

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)