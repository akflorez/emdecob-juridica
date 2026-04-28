import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

def create_database():
    try:
        # Intentamos conectar a la base de datos por defecto 'postgres' o 'emdecob_consultas'
        # para tener permisos de creaci?n.
        conn = psycopg2.connect(
            dbname='emdecob_consultas', 
            user='emdecob', 
            password='emdecob2026', 
            host='db', 
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Intentamos crear la base de datos juricob
        cur.execute('CREATE DATABASE juricob')
        print("Base de datos 'juricob' creada exitosamente.")
        
        cur.close()
        conn.close()
    except Exception as e:
        if "already exists" in str(e):
            print("La base de datos 'juricob' ya existe.")
        else:
            print(f"Error al crear la base de datos: {e}")

if __name__ == "__main__":
    create_database()
