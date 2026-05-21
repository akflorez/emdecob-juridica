from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from .base import Base  # assuming Base declarative base exists
from datetime import datetime

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String, index=True, nullable=False)
    ultima_actuacion = Column(Date, nullable=True)  # latest actuation date
    # Additional fields can be added as needed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Case id={self.id} radicado={self.radicado}>"
