
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Merging workspaces...")
        
        # Merge workspaces by name
        ws = conn.execute(text("SELECT name, COUNT(*) FROM workspaces GROUP BY name HAVING COUNT(*) > 1")).fetchall()
        for name, count in ws:
            all_ids = [r[0] for r in conn.execute(text("SELECT id FROM workspaces WHERE name = :n ORDER BY id"), {"n": name}).fetchall()]
            target_id = all_ids[0]
            others = all_ids[1:]
            
            # Move folders to target workspace
            conn.execute(text("UPDATE folders SET workspace_id = :target WHERE workspace_id IN :others"), {"target": target_id, "others": tuple(others)})
            
            # Delete others
            conn.execute(text("DELETE FROM workspaces WHERE id IN :others"), {"others": tuple(others)})
            print(f"Merged {count} workspaces for '{name}' into ID {target_id}")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
