import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Case, CaseEvent
from backend.service.publicaciones import (
    auto_queue_publicaciones,
    get_month_range,
    build_portal_search_url,
    extract_despacho_code,
    consultar_publicaciones_rango,
    parse_result_cards,
    filter_cards_by_despacho,
    filter_cards_by_category,
    open_detail,
    extract_text_content,
    find_radicado_in_context
)
import httpx

async def main():
    if len(sys.argv) < 2:
        print("Uso: python debug_publicacion.py <radicado>")
        sys.exit(1)
        
    radicado = sys.argv[1]
    
    db: Session = SessionLocal()
    case = db.query(Case).filter(Case.radicado == radicado).first()
    if not case:
        print(f"Error: No se encontró el caso con radicado {radicado} en la base de datos local.")
        db.close()
        sys.exit(1)
        
    print(f"===========================================================")
    print(f"DEBUG PUBLICACIONES PROCESALES (MODO ESTRICTO)")
    print(f"===========================================================")
    print(f"1. Radicado: {radicado}")
    despacho_codigo = extract_despacho_code(radicado)
    print(f"2. Despacho Calculado: {despacho_codigo}")
    
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).all()
    print(f"3. Actuaciones encontradas: {len(events)}")
    
    from backend.service.publicaciones import is_relevant_actuacion, get_search_months_for_actuacion
    relevant_events = [e for e in events if is_relevant_actuacion(e.title)]
    print(f"   Actuaciones relevantes detectadas: {len(relevant_events)}")
    
    meses_a_buscar = set()
    for ev in relevant_events:
        for year, month in get_search_months_for_actuacion(ev.event_date):
            meses_a_buscar.add(f"{year}-{month:02d}")
            
    print(f"4. Meses encolados: {sorted(list(meses_a_buscar))}")
    
    if not meses_a_buscar:
        print("No hay meses para buscar según actuaciones relevantes.")
        db.close()
        return

    mes = sorted(list(meses_a_buscar))[-1] # Tomar el más reciente para la prueba
    print(f"\n--- Ejecutando búsqueda simulada para el mes {mes} ---")
    
    year_str, month_str = mes.split('-')
    import calendar
    fecha_inicio_str = f"{year_str}-{month_str}-01"
    last_day = calendar.monthrange(int(year_str), int(month_str))[1]
    fecha_fin_str = f"{year_str}-{month_str}-{last_day:02d}"
    
    url_busqueda = build_portal_search_url(despacho_codigo, fecha_inicio_str, fecha_fin_str)
    print(f"5. URL Exacta Consultada:\n   {url_busqueda}")
    
    # Simular la llamada web
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://publicacionesprocesales.ramajudicial.gov.co/"
    }
    proxy_url = os.environ.get("RAMA_PROXY_URL")
    kwargs = {"headers": headers, "timeout": 30, "follow_redirects": True, "verify": False}
    if proxy_url: kwargs["proxy"] = proxy_url
    
    async with httpx.AsyncClient(**kwargs) as client:
        resp = await client.get(url_busqueda)
        if resp.status_code != 200:
            print("Error conectando a Rama Judicial.")
            return
            
        html = resp.text
        cards = parse_result_cards(html)
        print(f"6. Cantidad de tarjetas encontradas: {len(cards)}")
        
        filtered_by_despacho = filter_cards_by_despacho(cards, despacho_codigo)
        descartadas_despacho = len(cards) - len(filtered_by_despacho)
        
        filtered_by_category = filter_cards_by_category(filtered_by_despacho)
        descartadas_categoria = len(filtered_by_despacho) - len(filtered_by_category)
        
        print(f"7. Tarjetas descartadas:")
        print(f"   - Por despacho incorrecto: {descartadas_despacho}")
        print(f"   - Por categoría irrelevante: {descartadas_categoria}")
        print(f"8. Tarjetas a procesar: {len(filtered_by_category)}")
        
        for i, card in enumerate(filtered_by_category):
            print(f"\n[{i+1}/{len(filtered_by_category)}] Analizando: {card['title']}")
            print(f"   URL Detalle: {card['detail_url']}")
            
            detail_html = await open_detail(card)
            
            # Aqui deberíamos parsear los links de descarga
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(detail_html, "html.parser")
            docs = []
            for a in soup.find_all("a", href=True):
                if "get_file" in a["href"] or "documents" in a["href"]:
                    href = a["href"]
                    if not href.startswith("http"):
                        href = "https://publicacionesprocesales.ramajudicial.gov.co" + (href if href.startswith("/") else "/" + href)
                    docs.append((a.get_text(strip=True) or "Documento", href))
                    
            print(f"9. Documentos encontrados en tarjeta: {len(docs)}")
            
            for doc_name, doc_url in docs:
                print(f"   Descargando: {doc_name}...")
                text_content = await extract_text_content(doc_url, client)
                print(f"10. Fuente: {doc_url}")
                print(f"11. Texto extraído: {len(text_content)} caracteres")
                print(f"12. Calidad de extracción: {'Pobre' if len(text_content) < 500 else 'Aceptable/Buena'}")
                
                match_result = find_radicado_in_context(
                    text=text_content,
                    radicado=radicado,
                    demandante=case.demandante,
                    demandado=case.demandado
                )
                
                print(f"13. Mejor bloque de coincidencia:\n-----------------\n{match_result.texto_bloque_match[:200]}...\n-----------------")
                print(f"15. Score Calculado: {match_result.score}")
                print(f"16. Match Type: {match_result.match_type}")
                
                elem = match_result.elementos_detectados
                print(f"17. Demandante detectado: {'Sí' if elem.get('demandante') else 'No'}")
                print(f"18. Demandado detectado: {'Sí' if elem.get('demandado') else 'No'}")
                print(f"21. Estado Final: {match_result.estado_validacion}")
                print(f"22. Motivo: {match_result.reasons}")
                print(f"23. URL Documento: {doc_url}")
                print("-" * 50)

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
