import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database Connection - Strategy: Try Environment, then Local, then Remote
raw_url = os.getenv("DATABASE_URL", "")

def get_connection_url(url_str):
    if not url_str:
        return "postgresql://emdecob:emdecob2026@localhost:5432/juricob"
    
    # Clean shell-style variables if present
    clean_url = url_str.replace("${DB_USER:-emdecob}", "emdecob")
    clean_url = clean_url.replace("${DB_PASSWORD:-emdecob2026}", "emdecob2026")
    
    # Force localhost or IP for internal reliability
    if "@db" in clean_url or "db:5432" in clean_url:
        clean_url = clean_url.replace("@db", "@localhost")
    
    return clean_url

DATABASE_URL = get_connection_url(raw_url)

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