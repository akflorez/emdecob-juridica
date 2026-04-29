
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Starting ultra-fast mass unification...")
        
        # 1. Merge lists with same name (MASSIVE SQL)
        conn.execute(text("""
            WITH list_duplicates AS (
                SELECT name, MIN(id) as target_id, ARRAY_AGG(id) as all_ids
                FROM project_lists
                GROUP BY name
                HAVING COUNT(*) > 1
            ),
            moved_tasks AS (
                UPDATE tasks t
                SET list_id = ld.target_id
                FROM list_duplicates ld
                WHERE t.list_id = ANY(ld.all_ids)
                AND t.list_id != ld.target_id
                RETURNING t.id
            )
            SELECT count(*) FROM moved_tasks;
        """))
        
        conn.execute(text("""
            DELETE FROM project_lists
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, row_number() OVER (PARTITION BY name ORDER BY id) as rn
                    FROM project_lists
                ) t WHERE rn > 1
            );
        """))
        
        # 2. Merge folders with same name
        conn.execute(text("""
            WITH folder_duplicates AS (
                SELECT name, MIN(id) as target_id, ARRAY_AGG(id) as all_ids
                FROM folders
                GROUP BY name
                HAVING COUNT(*) > 1
            ),
            moved_lists AS (
                UPDATE project_lists pl
                SET folder_id = fd.target_id
                FROM folder_duplicates fd
                WHERE pl.folder_id = ANY(fd.all_ids)
                AND pl.folder_id != fd.target_id
                RETURNING pl.id
            )
            SELECT count(*) FROM moved_lists;
        """))
        
        conn.execute(text("""
            DELETE FROM folders
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, row_number() OVER (PARTITION BY name ORDER BY id) as rn
                    FROM folders
                ) t WHERE rn > 1
            );
        """))

        conn.commit()
        print("Mass unification completed successfully.")
            
except Exception as e:
    print(f"Error: {e}")
