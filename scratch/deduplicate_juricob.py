
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

def deduplicate():
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Starting deduplication of Folders and Lists in JURICOB...")
        
        # 1. Deduplicate Folders
        folders = conn.execute(text("SELECT name, COUNT(*) FROM folders GROUP BY name HAVING COUNT(*) > 1")).fetchall()
        for name, count in folders:
            f_ids = [r[0] for r in conn.execute(text("SELECT id FROM folders WHERE name = :n ORDER BY id"), {"n": name}).fetchall()]
            primary_f = f_ids[0]
            others = f_ids[1:]
            print(f"Merging Folder '{name}' (IDs {others} -> {primary_f})")
            
            # Move lists to primary folder
            conn.execute(text("UPDATE project_lists SET folder_id = :pf WHERE folder_id IN :others"), {"pf": primary_f, "others": tuple(others)})
            # Delete old folders
            conn.execute(text("DELETE FROM folders WHERE id IN :others"), {"others": tuple(others)})

        # 2. Deduplicate Lists within the same folder
        lists = conn.execute(text("SELECT name, folder_id, COUNT(*) FROM project_lists GROUP BY name, folder_id HAVING COUNT(*) > 1")).fetchall()
        for name, fid, count in lists:
            l_ids = [r[0] for r in conn.execute(text("SELECT id FROM project_lists WHERE name = :n AND folder_id = :fid ORDER BY id"), {"n": name, "fid": fid}).fetchall()]
            primary_l = l_ids[0]
            others = l_ids[1:]
            print(f"Merging List '{name}' in Folder {fid} (IDs {others} -> {primary_l})")
            
            # Move tasks to primary list
            conn.execute(text("UPDATE tasks SET list_id = :pl WHERE list_id IN :others"), {"pl": primary_l, "others": tuple(others)})
            # Delete old lists
            conn.execute(text("DELETE FROM project_lists WHERE id IN :others"), {"others": tuple(others)})

        # 3. Fix Encodings/Accents in names
        conn.execute(text("UPDATE project_lists SET name = REPLACE(name, '', 'E') WHERE name LIKE '%%'"))
        conn.execute(text("UPDATE folders SET name = REPLACE(name, '', 'E') WHERE name LIKE '%%'"))

        conn.commit()
        print("Deduplication finished.")

if __name__ == "__main__":
    try:
        deduplicate()
    except Exception as e:
        print(f"Error: {e}")
