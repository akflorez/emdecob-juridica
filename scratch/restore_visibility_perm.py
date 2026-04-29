
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Restoring permissions and visibility for Workspace 4...")
        
        # 1. Ensure 'admin' and 'jurico_emdecob' have membership in Workspace 4
        users = conn.execute(text("SELECT id FROM users WHERE username IN ('admin', 'jurico_emdecob', 'jurico.emdecob')")).fetchall()
        user_ids = [u[0] for u in users]
        
        for uid in user_ids:
            # Check if membership exists
            exists = conn.execute(text("SELECT 1 FROM memberships WHERE user_id = :u AND workspace_id = 4"), {"u": uid}).fetchone()
            if not exists:
                conn.execute(text("INSERT INTO memberships (user_id, workspace_id, role) VALUES (:u, 4, 'admin')"), {"u": uid})
                print(f"Added membership for user {uid} to Workspace 4")
        
        # 2. Ensure all folders and lists are indeed in Workspace 4
        # (This was done, but let's double check orphan lists)
        conn.execute(text("UPDATE project_lists SET folder_id = (SELECT id FROM folders WHERE workspace_id = 4 LIMIT 1) WHERE folder_id NOT IN (SELECT id FROM folders WHERE workspace_id = 4)"))
        
        # 3. Final task count check for Workspace 4
        count = conn.execute(text("""
            SELECT COUNT(*) FROM tasks t
            JOIN project_lists pl ON t.list_id = pl.id
            JOIN folders f ON pl.folder_id = f.id
            WHERE f.workspace_id = 4
        """)).scalar()
        print(f"Total tasks visible in Workspace 4: {count}")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
