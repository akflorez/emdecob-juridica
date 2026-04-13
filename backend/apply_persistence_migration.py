import pymysql
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ No DATABASE_URL found")
    exit(1)

engine = create_engine(DATABASE_URL)

print("🔍 Aplicando migración de persistencia...")
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE search_jobs ADD COLUMN is_imported BOOLEAN DEFAULT FALSE"))
        conn.commit()
        print("✅ Columna 'is_imported' añadida a 'search_jobs'")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("ℹ️ La columna 'is_imported' ya existe.")
        else:
            print(f"❌ Error: {e}")
