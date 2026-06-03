from backend.db import engine
from sqlalchemy import text

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    # 1. Crear empresa de pruebas
    c.execute(text("INSERT INTO companies (id, nombre, nit, limite_usuarios) VALUES (2, 'Empresa de Pruebas', '000000', 50) ON CONFLICT DO NOTHING"))
    
    # 2. Mover usuarios de prueba
    # testuser, fna_juridica (si no es de emdecob), y todos los de clickup (cu_...)
    c.execute(text("UPDATE users SET company_id = 2 WHERE username = 'testuser' OR username LIKE 'cu_%' OR username = 'fna_juridica'"))
    
    # 3. Asignar los demás a Emdecob (Empresa 1)
    # juricob, admin, akflorez
    c.execute(text("UPDATE users SET company_id = 1 WHERE username IN ('juricob', 'admin', 'akflorez')"))
    
    # superadmin se queda sin company_id (IS NULL)
    c.execute(text("UPDATE users SET company_id = NULL WHERE username = 'superadmin'"))
    
    print("Test company created and users moved.")
