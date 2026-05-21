from sqlalchemy import Column, Integer, String, Date, Text, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from .base import Base  # assuming a Base declarative base is defined in backend/models/base.py or similar
from datetime import datetime

class PublicacionProcesal(Base):
    __tablename__ = "publicaciones_procesales"

    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String, index=True, nullable=False)
    despacho_codigo = Column(String, nullable=False)
    fecha_actuacion = Column(Date, nullable=True)
    descripcion_actuacion = Column(String, nullable=True)
    fecha_inicio_busqueda = Column(Date, nullable=True)
    fecha_fin_busqueda = Column(Date, nullable=True)
    categoria_publicacion = Column(String, nullable=True)
    numero_estado = Column(String, nullable=True)
    fecha_publicacion = Column(Date, nullable=True)
    fecha_sincronizacion = Column(Date, nullable=True)
    url_detalle = Column(String, nullable=True)
    url_cuadro = Column(String, nullable=True)
    url_providencia = Column(String, nullable=True)
    texto_cuadro = Column(Text, nullable=True)
    texto_providencia = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    match_type = Column(String, nullable=True)
    match_fuerte = Column(Boolean, default=False)
    motivo_match = Column(JSON, nullable=True)
    estado_busqueda = Column(String, default="pending")
    error = Column(Text, nullable=True)
    fuente = Column(String, default="Publicaciones Procesales Rama Judicial")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PublicacionProcesal id={self.id} radicado={self.radicado}>"
