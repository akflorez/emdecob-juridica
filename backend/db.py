import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# ============================================================
# CONEXION A BASE DE DATOS
# URL externa Contabo (donde estan TODOS los datos reales)
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

    if "@localhost" in clean_url:
        clean_url = clean_url.replace("@localhost", "@db")

    # Si apunta al contenedor Docker interno, verificar si tiene datos.
    # Si no tiene datos, usar Contabo que tiene los datos reales.
    if "@db:" in clean_url or "@db/" in clean_url:
        try:
            test_engine = create_engine(clean_url, connect_args={"connect_timeout": 5})
            with test_engine.connect() as conn:
                count = conn.execute(text("SELECT count(*) FROM tasks")).scalar()
                if count == 0:
                    print(f"[DB] Docker interno tiene 0 tareas -> cambiando a Contabo externo")
                    return CONTABO_URL
                else:
                    print(f"[DB] Docker interno tiene {count} tareas -> OK")
                    return clean_url
        except Exception as e:
            print(f"[DB] Error al conectar a Docker interno ({e}) -> usando Contabo externo")
            return CONTABO_URL

    return clean_url

DATABASE_URL = get_connection_url(raw_url)
print(f"[DB] Conectando a: {DATABASE_URL[:50]}...")

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