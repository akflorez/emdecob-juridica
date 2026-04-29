
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Restoring permissions in workspace_members for Workspace 4...")
        
        # 1. Get user IDs
        users = conn.execute(text("SELECT id, username FROM users WHERE username IN ('admin', 'jurico_emdecob', 'jurico.emdecob')")).fetchall()
        
        for uid, uname in users:
            # Check if membership exists
            exists = conn.execute(text("SELECT 1 FROM workspace_members WHERE user_id = :u AND workspace_id = 4"), {"u": uid}).fetchone()
            if not exists:
                conn.execute(text("INSERT INTO workspace_members (user_id, workspace_id, role) VALUES (:u, 4, 'admin')"), {"u": uid})
                print(f"Added membership for user {uname} (ID {uid}) to Workspace 4")
            else:
                print(f"User {uname} already has access to Workspace 4")
        
        # 2. Final task count check for Workspace 4
        count = conn.execute(text("""
            SELECT COUNT(*) FROM tasks t
            JOIN project_lists pl ON t.list_id = pl.id
            JOIN folders f ON pl.folder_id = f.id
            WHERE f.workspace_id = 4
        """)).scalar()
        print(f"Total tasks now visible in Workspace 4: {count}")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
