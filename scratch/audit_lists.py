
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM project_lists")).scalar()
        print(f"Total project lists: {count}")
        
        dupes = conn.execute(text("SELECT name, count(*) FROM project_lists GROUP BY name HAVING count(*) > 1 ORDER BY count(*) DESC LIMIT 20")).fetchall()
        print(f"Top duplicates: {dupes}")

except Exception as e:
    print(f"Error: {e}")
