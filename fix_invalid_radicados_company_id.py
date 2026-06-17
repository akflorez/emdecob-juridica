"""
Script para actualizar el company_id de los registros existentes en invalid_radicados
que no tienen company_id asignado.

Los radicados en invalid_radicados coinciden con radicados en la tabla cases,
así que tomamos el company_id del Case correspondiente.

Ejecutar con: python fix_invalid_radicados_company_id.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.db import SessionLocal
from sqlalchemy import text

def fix_company_ids():
    db = SessionLocal()
    try:
        # Actualizar company_id en invalid_radicados tomándolo de cases
        result = db.execute(text("""
            UPDATE invalid_radicados ir
            SET company_id = c.company_id
            FROM cases c
            WHERE ir.radicado = c.radicado
              AND ir.company_id IS NULL
              AND c.company_id IS NOT NULL
        """))
        db.commit()
        updated = result.rowcount
        print(f"[OK] Actualizados {updated} registros en invalid_radicados con company_id")

        # Verificar cuántos quedan sin company_id
        remaining = db.execute(text(
            "SELECT COUNT(*) FROM invalid_radicados WHERE company_id IS NULL"
        )).scalar()
        print(f"[INFO] Registros sin company_id restantes: {remaining}")

        # Mostrar total de registros
        total = db.execute(text("SELECT COUNT(*) FROM invalid_radicados")).scalar()
        print(f"[INFO] Total de registros en invalid_radicados: {total}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_company_ids()
