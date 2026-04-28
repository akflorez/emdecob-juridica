import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database Connection - Prioritize environment variable (84.247.130.122 for remote server)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob")

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