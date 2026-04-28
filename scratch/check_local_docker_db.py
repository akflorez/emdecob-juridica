
import os
from sqlalchemy import create_engine

# Intento conectar a localhost:5432 (puerto mapeado de Docker)
LOCAL_POSTGRES = "postgresql://emdecob:emdecob2026@localhost:5432/juricob"

try:
    engine = create_engine(LOCAL_POSTGRES)
    with engine.connect() as conn:
        print("Success: Connected to LOCAL Docker Postgres at localhost:5432!")
except Exception as e:
    print(f"Failed to connect to local postgres: {e}")
