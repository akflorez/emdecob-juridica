import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

try:
    from backend.db import SessionLocal
    from backend.models import Case
except ImportError:
    # Try alternate import path
    from db import SessionLocal
    from models import Case

def fix_assignments():
    db = SessionLocal()
    fna_keywords = [
        "FONDO NACIONAL DEL AHORRO", 
        "FNA", 
        "FONDO NAL DEL AHORRO", 
        "F.N.A.", 
        "TRIADA", 
        "FONDO NACIONAL DEL AHORRO - FNA"
    ]
    
    # Get all cases currently assigned to Juricob (ID 2)
    jurico_cases = db.query(Case).filter(Case.user_id == 2).all()
    moved_count = 0
    
    print(f"Checking {len(jurico_cases)} cases assigned to Juricob...")
    
    for c in jurico_cases:
        match = False
        if c.demandante:
            name = c.demandante.upper()
            if any(kw in name for kw in fna_keywords):
                match = True
        
        if not match and c.demandado:
            name = c.demandado.upper()
            if any(kw in name for kw in fna_keywords):
                match = True
        
        # Any pending case (no juzgado) in Juricob is suspect, move to FNA as per user request
        if not match and c.juzgado is None:
            match = True
            
        if match:
            c.user_id = 1
            moved_count += 1
    
    db.commit()
    print(f"Successfully moved {moved_count} cases to FNA (ID 1).")
    
    # Also check for orphans that should be FNA
    orphan_fna = 0
    orphans = db.query(Case).filter(Case.user_id == None).all()
    for c in orphans:
        if c.demandante:
            name = c.demandante.upper()
            if any(kw in name for kw in fna_keywords):
                c.user_id = 1
                orphan_fna += 1
    
    db.commit()
    print(f"Successfully assigned {orphan_fna} orphan cases to FNA (ID 1).")
    
    db.close()

if __name__ == "__main__":
    fix_assignments()
