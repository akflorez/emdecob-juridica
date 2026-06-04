from sqlalchemy import text
from backend.db import engine

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    try:
        c.execute(text('ALTER TABLE case_events ADD COLUMN id_reg_actuacion BIGINT'))
        print('id_reg_actuacion added')
    except Exception as e:
        print(e)
    try:
        c.execute(text('ALTER TABLE case_events ADD COLUMN cons_actuacion BIGINT'))
        print('cons_actuacion added')
    except Exception as e:
        print(e)
    try:
        c.execute(text('ALTER TABLE case_events ADD COLUMN documentos_cache TEXT'))
        print('documentos_cache added')
    except Exception as e:
        print(e)
    try:
        c.execute(text('ALTER TABLE cases ADD COLUMN sync_pub_status VARCHAR(100)'))
        print('sync_pub_status added')
    except Exception as e:
        print(e)
    try:
        c.execute(text('ALTER TABLE cases ADD COLUMN sync_pub_progress INTEGER DEFAULT 0'))
        print('sync_pub_progress added')
    except Exception as e:
        print(e)
    try:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS sync_debug_logs (
                id SERIAL PRIMARY KEY,
                case_id INTEGER,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print('sync_debug_logs created')
    except Exception as e:
        print(e)

print('Done!')
