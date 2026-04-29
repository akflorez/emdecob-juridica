
import sqlalchemy
from sqlalchemy import create_engine, text
import os

NEON_URL = "postgresql://neondb_owner:npg_eWCA1gPd0ryo@ep-icy-thunder-akkkr42v.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require"
SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

print("--- STARTING NEON TO SERVER MIGRATION (V3) ---")

def clean_val(v):
    if isinstance(v, str):
        return v.replace('\u200b', '').strip()
    return v

try:
    engine_neon = create_engine(NEON_URL)
    engine_server = create_engine(SERVER_URL)
    
    with engine_neon.connect() as conn_neon, engine_server.connect() as conn_server:
        # 1. MIGRATE CASES
        print("Migrating Cases...")
        res_neon = conn_neon.execute(text("SELECT * FROM cases"))
        cols = res_neon.keys()
        neon_cases = res_neon.fetchall()
        
        migrated_cases = 0
        skipped_cases = 0
        
        existing_radicados = {clean_val(r[0]) for r in conn_server.execute(text("SELECT radicado FROM cases")).fetchall() if r[0]}
        
        for row in neon_cases:
            data = dict(zip(cols, row))
            rad = clean_val(data.get('radicado'))
            if not rad or rad in existing_radicados:
                skipped_cases += 1
                continue
            
            clean_data = {k: clean_val(v) for k, v in data.items() if k != 'id'}
            placeholders = ", ".join([f":{k}" for k in clean_data.keys()])
            columns = ", ".join(clean_data.keys())
            
            try:
                conn_server.execute(text(f"INSERT INTO cases ({columns}) VALUES ({placeholders})"), clean_data)
                conn_server.commit()
                existing_radicados.add(rad)
                migrated_cases += 1
            except Exception as e:
                print(f"Error inserting case {rad}: {e}")
                conn_server.rollback()
                skipped_cases += 1
            
        print(f"Cases: Migrated {migrated_cases}, Skipped {skipped_cases}")

        # 2. MIGRATE TASKS
        print("Migrating Tasks...")
        res_neon_tasks = conn_neon.execute(text("SELECT * FROM tasks"))
        cols_tasks = res_neon_tasks.keys()
        neon_tasks = res_neon_tasks.fetchall()
        
        existing_clickup_ids = {r[0] for r in conn_server.execute(text("SELECT clickup_id FROM tasks WHERE clickup_id IS NOT NULL")).fetchall()}
        
        migrated_tasks = 0
        skipped_tasks = 0
        for row in neon_tasks:
            data = dict(zip(cols_tasks, row))
            cid = data.get('clickup_id')
            if cid and cid in existing_clickup_ids:
                skipped_tasks += 1
                continue
            
            clean_data = {k: clean_val(v) for k, v in data.items() if k != 'id'}
            placeholders = ", ".join([f":{k}" for k in clean_data.keys()])
            columns = ", ".join(clean_data.keys())
            
            try:
                conn_server.execute(text(f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"), clean_data)
                conn_server.commit()
                if cid: existing_clickup_ids.add(cid)
                migrated_tasks += 1
            except Exception as e:
                print(f"Error inserting task {cid}: {e}")
                conn_server.rollback()
                skipped_tasks += 1
            
        print(f"Tasks: Migrated {migrated_tasks}, Skipped {skipped_tasks}")

        # 3. MIGRATE CASE EVENTS
        print("Migrating Case Events...")
        rad_to_id = {clean_val(r[0]): r[1] for r in conn_server.execute(text("SELECT radicado, id FROM cases")).fetchall() if r[0]}
        neon_id_to_rad = {r[0]: clean_val(r[1]) for r in conn_neon.execute(text("SELECT id, radicado FROM cases")).fetchall() if r[1]}
        
        res_neon_events = conn_neon.execute(text("SELECT * FROM case_events"))
        cols_events = res_neon_events.keys()
        neon_events = res_neon_events.fetchall()
        
        migrated_events = 0
        skipped_events = 0
        
        existing_hashes = {r[0] for r in conn_server.execute(text("SELECT event_hash FROM case_events WHERE event_hash IS NOT NULL")).fetchall()}
        
        for row in neon_events:
            data = dict(zip(cols_events, row))
            h = data.get('event_hash')
            if h and h in existing_hashes:
                skipped_events += 1
                continue
            
            neon_case_id = data.get('case_id')
            rad = neon_id_to_rad.get(neon_case_id)
            server_case_id = rad_to_id.get(rad)
            
            if not server_case_id:
                skipped_events += 1
                continue
                
            data['case_id'] = server_case_id
            clean_data = {k: clean_val(v) for k, v in data.items() if k != 'id'}
            placeholders = ", ".join([f":{k}" for k in clean_data.keys()])
            columns = ", ".join(clean_data.keys())
            
            try:
                conn_server.execute(text(f"INSERT INTO case_events ({columns}) VALUES ({placeholders})"), clean_data)
                conn_server.commit()
                if h: existing_hashes.add(h)
                migrated_events += 1
            except Exception as e:
                # print(f"Error inserting event {h}: {e}")
                conn_server.rollback()
                skipped_events += 1
            
        print(f"Events: Migrated {migrated_events}, Skipped {skipped_events}")

    print("--- MIGRATION V3 COMPLETED ---")

except Exception as e:
    print(f"MIGRATION ERROR: {e}")
    import traceback
    traceback.print_exc()
