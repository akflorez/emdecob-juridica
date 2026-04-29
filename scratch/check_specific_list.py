
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        folder_name = "PAUL JAMES SOTO JARAMILLO"
        list_name = "ALFREDO EDUARDO CAVADIA SANCHEZ"
        
        res = conn.execute(text("""
            SELECT l.id, l.name, f.name 
            FROM project_lists l
            JOIN folders f ON l.folder_id = f.id
            WHERE l.name = :ln AND f.name = :fn
        """), {"ln": list_name, "fn": folder_name}).fetchall()
        for r in res:
            print(f"Found List ID: {r[0]} | List: {r[1]} | Folder: {r[2]}")
            t_count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE list_id = :lid"), {"lid": r[0]}).scalar()
            print(f"  Tasks in DB for this ID: {t_count}")
            
except Exception as e:
    print(f"Error: {e}")
