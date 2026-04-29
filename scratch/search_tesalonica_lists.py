
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, name FROM folders WHERE name ILIKE '%TESALONICA%'")).fetchall()
        print("Folders matching TESALONICA in juricob:")
        for r in res:
            print(f"- ID: {r[0]} | Name: {r[1]}")
            # Get lists in this folder
            lists = conn.execute(text("SELECT id, name FROM project_lists WHERE folder_id = :fid"), {"fid": r[0]}).fetchall()
            for l in lists:
                print(f"  -> List ID: {l[0]} | Name: {l[1]}")
            
except Exception as e:
    print(f"Error: {e}")
