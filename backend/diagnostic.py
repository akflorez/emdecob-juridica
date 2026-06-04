import os
import sys
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Base
from backend.db import SQLALCHEMY_DATABASE_URL

def run_diagnostic():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    metadata = Base.metadata
    
    missing_columns_by_table = {}
    
    print("=== STARTING DIAGNOSTIC ===")
    
    for table_name, table in metadata.tables.items():
        if not inspector.has_table(table_name):
            print(f"Table missing entirely: {table_name}")
            continue
            
        existing_cols = {c['name'] for c in inspector.get_columns(table_name)}
        model_cols = {c.name: c for c in table.columns}
        
        missing_cols = []
        for col_name, col_obj in model_cols.items():
            if col_name not in existing_cols:
                missing_cols.append(col_name)
                
        if missing_cols:
            print(f"Table '{table_name}' is missing columns: {missing_cols}")
            missing_columns_by_table[table_name] = missing_cols
        else:
            print(f"Table '{table_name}' has all model columns.")
            
    print("=== END OF DIAGNOSTIC ===")
    return missing_columns_by_table

if __name__ == "__main__":
    run_diagnostic()
