import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database Connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    db_user = os.getenv("DB_USER", "emdecob")
    db_pass = os.getenv("DB_PASSWORD", "emdecob2026")
    db_name = "juricob" # BASE DE DATOS OFICIAL DEFINITIVA
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    
    DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    print(f"[DB] URL construida: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

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