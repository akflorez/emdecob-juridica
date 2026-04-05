import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database Connection
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_URL")

if not DATABASE_URL:
    print("⚠️ ADVERTENCIA: Falta configurar DATABASE_URL o NEON_URL en el entorno. Usando base de datos predeterminada.")
    DATABASE_URL = "sqlite:////tmp/fallback.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=280,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()