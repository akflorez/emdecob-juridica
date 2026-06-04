import os
import sys
from sqlalchemy import create_engine, inspect

sys.path.append(os.getcwd())
from backend.db import DATABASE_URL

def main():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    table_name = "case_publications"
    if table_name not in inspector.get_table_names():
        print(f"Table '{table_name}' does not exist.")
        return
        
    print(f"\n--- Columns in {table_name} ---")
    for col in inspector.get_columns(table_name):
        print(f"Name: {col['name']} | Type: {col['type']} | Nullable: {col['nullable']}")
        
    print(f"\n--- Unique Constraints in {table_name} ---")
    for uc in inspector.get_unique_constraints(table_name):
        print(f"Constraint: {uc['name']} | Columns: {uc['column_names']}")
        
    print(f"\n--- Indexes in {table_name} ---")
    for idx in inspector.get_indexes(table_name):
        print(f"Index: {idx['name']} | Columns: {idx['column_names']} | Unique: {idx['unique']}")

if __name__ == "__main__":
    main()
