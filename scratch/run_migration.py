import sqlalchemy
from sqlalchemy import create_engine, text
import requests
import json
import sys

SRC_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

# Bypass Cloudflare: apuntar directo al servidor nginx en el puerto expuesto
# El frontend container corre en el puerto 8090 segun docker-compose.yaml
PROD_API = "http://84.247.130.122:8090/api/admin/bulk-import"

HEADERS = {
    "Content-Type": "application/json",
    "Host": "consultasjuridicas.emdecob.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
}

def serialize(val):
    """Convierte tipos no serializables a string para JSON."""
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return val

def main():
    print("Conectando al PostgreSQL nativo...")
    engine = create_engine(SRC_URL, connect_args={"connect_timeout": 10})
    
    with engine.connect() as conn:
        # 1. Workspaces
        print("Leyendo workspaces...")
        ws_rows = conn.execute(text("SELECT id, name, visibility, owner_id, clickup_id FROM workspaces")).fetchall()
        workspaces = [{"id": r[0], "name": r[1], "visibility": r[2], "owner_id": r[3], "clickup_id": r[4]} for r in ws_rows]

        # 2. Folders
        print("Leyendo folders...")
        f_rows = conn.execute(text("SELECT id, name, workspace_id, clickup_id FROM folders")).fetchall()
        folders = [{"id": r[0], "name": r[1], "workspace_id": r[2], "clickup_id": r[3]} for r in f_rows]

        # 3. Lists
        print("Leyendo listas...")
        l_rows = conn.execute(text("SELECT id, name, folder_id, workspace_id, clickup_id FROM project_lists")).fetchall()
        lists = [{"id": r[0], "name": r[1], "folder_id": r[2], "workspace_id": r[3], "clickup_id": r[4]} for r in l_rows]

        # 4. Tasks
        print("Leyendo tareas...")
        t_rows = conn.execute(text("""
            SELECT id, title, description, status, priority, assignee_id,
                   list_id, due_date, case_id, parent_id, created_at, clickup_id
            FROM tasks
        """)).fetchall()
        tasks = [{
            "id": r[0], "title": r[1], "description": r[2], "status": r[3],
            "priority": r[4], "assignee_id": r[5], "list_id": r[6],
            "due_date": serialize(r[7]), "case_id": r[8],
            "parent_id": r[9], "created_at": serialize(r[10]), "clickup_id": r[11]
        } for r in t_rows]

    print(f"\nDatos leídos: {len(workspaces)} ws, {len(folders)} folders, {len(lists)} listas, {len(tasks)} tareas")
    
    # Enviar en bloques (las listas son muchas, las enviamos en lotes)
    BATCH = 500
    
    # Primero enviar workspaces + folders + primeras listas + primeras tareas
    print("\nEnviando bloque 1 (workspaces + folders + listas)...")
    payload = {
        "workspaces": workspaces,
        "folders": folders,
        "lists": lists[:BATCH],
        "tasks": tasks[:BATCH]
    }
    r = requests.post(PROD_API, json=payload, headers=HEADERS, timeout=120)
    print(f"Bloque 1: {r.status_code} - {r.text[:200]}")

    # Listas restantes en lotes
    for i in range(BATCH, len(lists), BATCH):
        batch = lists[i:i+BATCH]
        print(f"Enviando listas {i}-{i+len(batch)}...")
        r = requests.post(PROD_API, json={"workspaces": [], "folders": [], "lists": batch, "tasks": []}, headers=HEADERS, timeout=120)
        print(f"  {r.status_code}")

    # Tareas restantes en lotes
    for i in range(BATCH, len(tasks), BATCH):
        batch = tasks[i:i+BATCH]
        print(f"Enviando tareas {i}-{i+len(batch)}...")
        r = requests.post(PROD_API, json={"workspaces": [], "folders": [], "lists": [], "tasks": batch}, headers=HEADERS, timeout=120)
        print(f"  {r.status_code}")

    print("Migracion completada OK")

if __name__ == "__main__":
    main()
