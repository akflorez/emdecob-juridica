import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database Connection - Prioritize environment variable
raw_url = os.getenv("DATABASE_URL", "")

# Robust parsing for shell-style variables like ${DB_USER:-emdecob}
if "${" in raw_url:
    # Si la variable viene con formato de shell (comun en Docker), limpiarla manualmente
    raw_url = raw_url.replace("${DB_USER:-emdecob}", "emdecob")
    raw_url = raw_url.replace("${DB_PASSWORD:-emdecob2026}", "emdecob2026")
    raw_url = raw_url.replace("@db:", "@84.247.130.122:") # Asegurar IP si el host 'db' no resuelve
    
if not raw_url or "db:5432" in raw_url:
    # Si esta vacio o usa el host interno 'db' que a veces falla, usar la IP directa de produccion
    DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
else:
    DATABASE_URL = raw_url

# Configuración optimizada para multi-usuario y alto rendimiento
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,          # Conexiones base en el pool
    max_overflow=10,       # Conexiones extra permitidas en picos
    pool_timeout=30,       # Espera máxima por una conexión
    pool_recycle=1800,     # Reciclar conexiones cada 30 min para evitar desconexiones de Postgres
    pool_pre_ping=True,    # Verificar conexión antes de usarla (evita 500s por socket cerrado)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()