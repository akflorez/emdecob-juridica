
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("=== DIAGNOSTICO COMPLETO DE JERARQUIA ===")
        
        # 1. Cuantos workspaces hay?
        ws_count = conn.execute(text("SELECT count(*) FROM workspaces")).scalar()
        print(f"Workspaces: {ws_count}")
        
        # 2. Cuantas carpetas hay?
        folder_count = conn.execute(text("SELECT count(*) FROM folders")).scalar()
        print(f"Folders: {folder_count}")
        
        # 3. Cuantas listas hay?
        list_count = conn.execute(text("SELECT count(*) FROM project_lists")).scalar()
        print(f"Lists: {list_count}")
        
        # 4. La lista 26 (Cavadia) a que carpeta y workspace pertenece?
        list_26 = conn.execute(text("""
            SELECT pl.id, pl.name, pl.folder_id, pl.workspace_id,
                   f.name as folder_name, f.workspace_id as folder_ws_id,
                   w.id as ws_id, w.name as ws_name
            FROM project_lists pl
            LEFT JOIN folders f ON pl.folder_id = f.id
            LEFT JOIN workspaces w ON f.workspace_id = w.id
            WHERE pl.id = 26
        """)).fetchone()
        print(f"\nLista 26 (Cavadia): {list_26}")
        
        # 5. Cuantas listas tienen folder_id NULL o workspace_id NULL?
        orphan_lists = conn.execute(text("SELECT count(*) FROM project_lists WHERE folder_id IS NULL AND workspace_id IS NULL")).scalar()
        orphan_folder = conn.execute(text("SELECT count(*) FROM project_lists WHERE folder_id IS NULL")).scalar()
        print(f"\nListas sin folder: {orphan_folder}")
        print(f"Listas sin folder NI workspace: {orphan_lists}")
        
        # 6. La primera carpeta del primer workspace
        first_ws = conn.execute(text("SELECT id, name FROM workspaces LIMIT 3")).fetchall()
        print(f"\nPrimeros workspaces: {first_ws}")
        
        if first_ws:
            ws_id = first_ws[0][0]
            first_folders = conn.execute(text("SELECT id, name FROM folders WHERE workspace_id = :w LIMIT 3"), {"w": ws_id}).fetchall()
            print(f"Carpetas del workspace {ws_id}: {first_folders}")

except Exception as e:
    print(f"Error: {e}")
