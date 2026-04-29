import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# =============================================================
# CONFIGURACION DE BASE DE DATOS
# El PostgreSQL NATIVO del servidor tiene las 1034 tareas reales.
# Desde Docker en Linux, el host nativo se accede via host.docker.internal
# (habilitado con extra_hosts: host-gateway en docker-compose.yaml)
# =============================================================

raw_url = os.getenv("DATABASE_URL", "")

def get_connection_url(url_str):
    # URL del PostgreSQL nativo via Docker host gateway
    NATIVE_PG_URL = "postgresql://emdecob:emdecob2026@host.docker.internal:5432/juricob"

    if not url_str:
        return NATIVE_PG_URL

    # Limpiar variables de shell literal si aparecen
    clean_url = url_str.replace("${DB_USER:-emdecob}", "emdecob")
    clean_url = clean_url.replace("${DB_PASSWORD:-emdecob2026}", "emdecob2026")

    # Si apunta al Docker interno vacío o localhost, usar el PostgreSQL nativo del host
    if "@db:" in clean_url or "@db/" in clean_url or "@localhost" in clean_url:
        return NATIVE_PG_URL

    return clean_url

DATABASE_URL = get_connection_url(raw_url)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()