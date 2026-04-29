
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Final unification of folders and lists...")
        
        # 1. Deduplicate project_lists by name
        lists = conn.execute(text("SELECT name, COUNT(*) FROM project_lists GROUP BY name HAVING COUNT(*) > 1")).fetchall()
        for name, count in lists:
            all_ids = [r[0] for r in conn.execute(text("SELECT id FROM project_lists WHERE name = :n ORDER BY id"), {"n": name}).fetchall()]
            target_id = all_ids[0]
            others = all_ids[1:]
            
            # Move tasks to target
            conn.execute(text("UPDATE tasks SET list_id = :target WHERE list_id IN :others"), {"target": target_id, "others": tuple(others)})
            
            # Delete others
            conn.execute(text("DELETE FROM project_lists WHERE id IN :others"), {"others": tuple(others)})
            print(f"Merged {count} lists for '{name}' into ID {target_id}")

        # 2. Deduplicate folders by name
        folders = conn.execute(text("SELECT name, COUNT(*) FROM folders GROUP BY name HAVING COUNT(*) > 1")).fetchall()
        for name, count in folders:
            all_ids = [r[0] for r in conn.execute(text("SELECT id FROM folders WHERE name = :n ORDER BY id"), {"n": name}).fetchall()]
            target_id = all_ids[0]
            others = all_ids[1:]
            
            # Move lists to target folder
            conn.execute(text("UPDATE project_lists SET folder_id = :target WHERE folder_id IN :others"), {"target": target_id, "others": tuple(others)})
            
            # Delete others
            conn.execute(text("DELETE FROM folders WHERE id IN :others"), {"others": tuple(others)})
            print(f"Merged {count} folders for '{name}' into ID {target_id}")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
