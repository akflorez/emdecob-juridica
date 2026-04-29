
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Cleaning duplicate workspaces in the OLD database (emdecob_consultas)...")
        
        # Merge workspaces by name in the OLD DB too
        ws = conn.execute(text("SELECT name, COUNT(*) FROM workspaces GROUP BY name HAVING COUNT(*) > 1")).fetchall()
        for name, count in ws:
            all_ids = [r[0] for r in conn.execute(text("SELECT id FROM workspaces WHERE name = :n ORDER BY id"), {"n": name}).fetchall()]
            target_id = all_ids[0]
            others = all_ids[1:]
            
            # Move folders to target workspace
            conn.execute(text("UPDATE folders SET workspace_id = :target WHERE workspace_id IN :others"), {"target": target_id, "others": tuple(others)})
            
            # Delete others
            conn.execute(text("DELETE FROM workspaces WHERE id IN :others"), {"others": tuple(others)})
            print(f"Merged {count} workspaces in OLD DB")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
