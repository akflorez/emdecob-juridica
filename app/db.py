import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Neon PostgreSQL
DATABASE_URL = os.getenv("NEON_URL")

if not DATABASE_URL:
    raise ValueError("❌ Falta configurar NEON_URL en el archivo .env")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=280,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()