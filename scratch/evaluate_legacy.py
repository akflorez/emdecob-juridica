import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Connect to emdecob_consultas
db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

pub_id = 2805

with engine.connect() as conn:
    # Get publication details
    query = text("""
        SELECT cp.id, cp.case_id, c.radicado, c.demandante, c.demandado,
        cp.texto_fuente_principal, cp.url_fuente_principal, cp.match_score, cp.estado_validacion
        FROM case_publications cp
        JOIN cases c ON cp.case_id = c.id
        WHERE cp.id = :pub_id
    """)
    res = conn.execute(query, {"pub_id": pub_id}).fetchone()
    if not res:
        print(f"Publication {pub_id} not found.")
        exit(1)
        
    pub_id, case_id, radicado, demandante, demandado, text_content, url, old_score, old_estado = res
    print(f"Loaded publication ID: {pub_id}")
    print(f"Radicado: {radicado}")
    print(f"Demandante: {demandante}")
    print(f"Demandado: {demandado}")
    print(f"URL: {url}")
    print(f"Old Score: {old_score}, Old Estado: {old_estado}")
    print(f"Text length: {len(text_content) if text_content else 0}")
    
    if not text_content:
        # If text is empty, try to download and extract text
        import httpx
        from bs4 import BeautifulSoup
        import asyncio
        from backend.service.publicaciones import extract_text_content
        
        async def fetch_text():
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                return await extract_text_content(url, client)
                
        print("Text content is empty, attempting to download and extract text...")
        text_content = asyncio.run(fetch_text())
        print(f"Downloaded text length: {len(text_content)}")

    # Run classify_document_match
    from backend.service.publicaciones import classify_document_match
    match = classify_document_match(
        text_content, 
        radicado, 
        demandante=demandante or "", 
        demandado=demandado or "", 
        is_filtered_source=True
    )
    print("\n--- RE-EVALUATION RESULT ---")
    print(f"Is Valid: {match.is_valid}")
    print(f"Match Type: {match.match_type}")
    print(f"Reasons: {match.reasons}")
    print(f"Score: {match.score}")
    print(f"Validation State: {match.estado_validacion}")
    print(f"Evidence text excerpt: {match.texto_bloque_match[:150]}...")
    
    # Update publication in DB
    update_query = text("""
        UPDATE case_publications
        SET match_score = :score,
        estado_validacion = :estado,
        match_type = :match_type,
        motivo_match = :reasons,
        texto_bloque_match = :bloque,
        requiere_revision = :req_rev
        WHERE id = :pub_id
    """)
    conn.execute(update_query, {
        "score": match.score,
        "estado": match.estado_validacion,
        "match_type": match.match_type,
        "reasons": match.reasons,
        "bloque": match.texto_bloque_match,
        "req_rev": match.estado_validacion == "requiere_revision",
        "pub_id": pub_id
    })
    conn.commit()
    print("\nSuccessfully updated DB!")
