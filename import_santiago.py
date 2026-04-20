import os
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Case, User

def import_santiago_file():
    file_path = "radicados santiago.xlsx"
    if not os.path.exists(file_path):
        print(f"Error: No se encuentra el archivo {file_path}")
        return

    db: Session = SessionLocal()
    try:
        # Buscar usuario jurico_emdecob
        user = db.query(User).filter(User.username == "jurico_emdecob").first()
        if not user:
            print("Error: El usuario 'jurico_emdecob' no existe. Ejecuta el servidor primero o crea el usuario.")
            return
        
        user_id = user.id
        print(f"Importando para usuario: {user.username} (ID: {user_id})")

        # Leer Excel
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        rad_col = next((c for c in df.columns if c in ["radicado", "numero", "proceso"]), None)
        if not rad_col:
            print("Error: No se encontró la columna 'Radicado' en el Excel.")
            return

        created = 0
        skipped = 0

        for _, row in df.iterrows():
            radicado = str(row.get(rad_col)).strip()
            if not radicado or radicado == "nan":
                skipped += 1
                continue
            
            # Limpiar radicado (debe tener 23 dígitos usualmente)
            radicado = radicado.replace(".0", "")
            
            # Evitar duplicados para este usuario
            exists = db.query(Case).filter(Case.radicado == radicado, Case.user_id == user_id).first()
            if not exists:
                db.add(Case(radicado=radicado, user_id=user_id, abogado="santiago quintero"))
                created += 1
            else:
                skipped += 1
        
        db.commit()
        print(f"Importación finalizada: {created} creados, {skipped} omitidos/duplicados.")

    except Exception as e:
        print(f"Error durante la importación: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_santiago_file()
