import asyncio
import httpx
import sys
import os
from bs4 import BeautifulSoup

sys.path.append(os.getcwd())
from backend.service.publicaciones import (
    build_portal_search_url,
    HEADERS,
    parse_result_cards,
    detect_main_sources,
    extract_text_content,
    validate_strong_match
)

async def main():
    # 1. Search with delta=100
    search_url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30") + "&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_delta=100"
    print(f"Querying search URL: {search_url}")
    
    radicado = "11001400300720250052200"
    demandante = "FONDO NACIONAL DEL AHORRO S.A."
    demandado = "JORGE ENRIQUE TALERO CORTES"
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(search_url)
        if resp.status_code != 200:
            print(f"Search failed with code {resp.status_code}")
            return
            
        cards = parse_result_cards(resp.text)
        print(f"Found {len(cards)} cards for June 2025.")
        
        for idx, card in enumerate(cards):
            title = card["title"]
            date_pub = card["fecha_publicacion"]
            detail_url = card["detail_url"]
            print(f"\n[{idx+1:02d}] CARD: {title} | Date: {date_pub}")
            
            # We want to check cards with dates around June 5/6, or maybe all "ESTADO" cards
            if "ESTADO" in title.upper() or "FIJACION" in title.upper():
                print(f"Fetching detail: {detail_url}")
                detail_resp = await client.get(detail_url)
                if detail_resp.status_code != 200:
                    print(f"Failed to fetch detail for {title}")
                    continue
                
                sources = detect_main_sources(detail_resp.text)
                print(f"Main sources detected: {sources}")
                
                for source in sources:
                    s_url = source["url"]
                    s_tipo = source["tipo"]
                    print(f"Downloading source ({s_tipo}): {s_url}")
                    try:
                        doc_text = await extract_text_content(s_url, client)
                        print(f"Text size: {len(doc_text)} characters")
                        
                        # Test matching
                        match = validate_strong_match(doc_text, radicado, demandante, demandado)
                        print(f"MATCH RESULT: is_valid={match.is_valid} | type={match.match_type} | reasons={match.reasons}")
                        
                        if match.is_valid:
                            print("SUCCESS! Case matched in this card.")
                    except Exception as e:
                        print(f"Error checking source: {e}")

if __name__ == "__main__":
    asyncio.run(main())
