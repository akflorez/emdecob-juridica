import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database Connection
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_URL")

if not DATABASE_URL:
    db_user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "emdecob")
    db_pass = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "emdecob2026")
    db_name = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "juricob")
    db_host = os.getenv("DB_HOST", "db")
    
    # Intentar construir URL de Postgres si hay indicios de que estamos en Docker
    if db_user and db_pass:
        DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
        print(f"🔗 [DB] Construida URL de base de datos: postgresql://{db_user}:***@{db_host}:5432/{db_name}")
    else:
        print("⚠️ ADVERTENCIA: Falta configurar DATABASE_URL. Usando SQLite fallback.")
        DATABASE_URL = "sqlite:////tmp/fallback.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=280,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()