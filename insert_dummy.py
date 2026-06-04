from sqlalchemy import text
from backend.db import engine

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    try:
        c.execute(text("INSERT INTO case_events (case_id, event_date, title, detail, event_hash, con_documentos, id_reg_actuacion) VALUES (409, '2026-06-03', 'Auto de prueba (AI)', 'Esta es una actuación de prueba insertada directamente en la base de datos para verificar que la interfaz sí las muestra.', 'hash123456', false, 999999) ON CONFLICT (case_id, event_hash) DO NOTHING"))
        print('INSERTED')
    except Exception as e:
        print(e)
