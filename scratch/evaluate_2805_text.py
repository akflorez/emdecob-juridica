import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.getcwd())
from backend.models import CasePublication, Case
from backend.service.publicaciones import classify_document_match

def main():
    db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    pub = db.query(CasePublication).filter(CasePublication.id == 2805).first()
    case = db.query(Case).filter(Case.id == 456).first()
    
    if not pub or not case:
        print("Publication or Case not found.")
        return
        
    print(f"Radicado: {case.radicado}")
    print(f"Demandante: {case.demandante}")
    print(f"Demandado: {case.demandado}")
    
    # Classify match
    res = classify_document_match(
        pub.texto_fuente_principal,
        case.radicado,
        case.demandante or "",
        case.demandado or "",
        is_filtered_source=True
    )
    
    print("\n--- Match Result ---")
    print(f"Is valid: {res.is_valid}")
    print(f"Match Type: {res.match_type}")
    print(f"Score: {res.score}")
    print(f"Estado validacion: {res.estado_validacion}")
    print(f"Reasons: {res.reasons}")
    print(f"Snippet: {res.texto_bloque_match}")
    print(f"Elementos: {res.elementos_detectados}")
    
    # Let's search for some substrings manually in text
    txt = (pub.texto_fuente_principal or "").lower()
    print("\n--- Substring Searches (case insensitive) ---")
    print(f"Contains '595': {'595' in txt}")
    print(f"Contains '00595': {'00595' in txt}")
    print(f"Contains '2025': {'2025' in txt}")
    print(f"Contains 'salcedo': {'salcedo' in txt}")
    print(f"Contains 'fondo': {'fondo' in txt}")
    print(f"Contains 'ahorro': {'ahorro' in txt}")
    print(f"Contains 'luis': {'luis' in txt}")

if __name__ == "__main__":
    main()
