import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# ============================================================
# CONEXION A BASE DE DATOS
# Los datos REALES están en Contabo. El Docker interno está vacío.
# ============================================================
CONTABO_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

raw_url = os.getenv("DATABASE_URL", "")

def get_connection_url(url_str):
    if not url_str:
        print("[DB] Sin DATABASE_URL -> usando Contabo externo")
        return CONTABO_URL

    # Limpiar variables de shell literal si aparecen
    clean_url = url_str.replace("${DB_USER:-emdecob}", "emdecob")
    clean_url = clean_url.replace("${DB_PASSWORD:-emdecob2026}", "emdecob2026")

    # Si apunta al contenedor Docker interno ('db'), los datos están en Contabo
    # Redireccionar automáticamente a la base de datos real
    if "@db:" in clean_url or "@db/" in clean_url:
        print("[DB] DATABASE_URL apunta a Docker interno (vacio) -> redirigiendo a Contabo externo")
        return CONTABO_URL

    if "@localhost" in clean_url:
        print("[DB] DATABASE_URL apunta a localhost -> redirigiendo a Contabo externo")
        return CONTABO_URL

    print(f"[DB] Usando DATABASE_URL del entorno: {clean_url[:40]}...")
    return clean_url

DATABASE_URL = get_connection_url(raw_url)
print(f"[DB] URL final: {DATABASE_URL[:50]}...")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()