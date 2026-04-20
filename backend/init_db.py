import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

from backend.db import engine, Base
from backend.models import (
    Workspace, WorkspaceMember, Folder, ProjectList, Task, TaskComment, TaskAttachment
)

def init():
    print("Iniciando creacion de tablas (EMDECOB Task)...")
    try:
        # Esto creara todas las tablas que falten en el motor configurado
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas/verificadas exitosamente.")
    except Exception as e:
        print(f"Error al crear tablas: {e}")

if __name__ == "__main__":
    init()
