import httpx
import asyncio
from bs4 import BeautifulSoup
import re
from datetime import datetime, date, timedelta
import hashlib
from typing import List, Dict, Optional
import random

# Configuración
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales"
SEARCH_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Connection": "keep-alive",
}

def normalize_text(text: str) -> str:
    if not text: return ""
    import unicodedata
    return "".join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn').strip()

def is_relevant_actuacion(text: str) -> bool:
    text = normalize_text(text)
    keywords = ["auto", "notificacion", "estado", "traslado", "termino", "requiere", "despacho", "edicto", "fijacion"]
    return any(k in text for k in keywords)

async def consultar_publicaciones_rango(radicado_completo: str, fecha_act_str: str, demandado: str = ""):
    """
    Busca publicaciones siguiendo el 'paso a paso' del usuario:
    1. Filtra por Despacho (primeros 12 dígitos).
    2. Filtra por rango de fecha (Mes de la actuación).
    3. Busca el radicado (Año-Consecutivo) en los resultados.
    """
    results = []
    if not radicado_completo or len(radicado_completo.strip()) < 21:
        return []

    rad_clean = radicado_completo.strip().replace(" ", "")
    id_despacho = rad_clean[:12]
    
    # Rango de fechas: Desde la fecha de actuación hasta 30 días después
    try:
        f_base = datetime.strptime(fecha_act_str[:10], "%Y-%m-%d")
    except:
        f_base = datetime.now() - timedelta(days=5)

    f_ini_str = f_base.strftime("%d/%m/%Y")
    f_fin_str = (f_base + timedelta(days=30)).strftime("%d/%m/%Y")

    print(f"[search] [publicaciones.py] Buscando en Despacho {id_despacho} rango [{f_ini_str} - {f_fin_str}]")

    # Parámetros para la búsqueda avanzada del portal
    params = {
        "idDespacho": id_despacho,
        "fechaInicio": f_ini_str,
        "fechaFinal": f_fin_str,
        "action": "busqueda"
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True, verify=False) as client:
            resp = await client.get(SEARCH_URL, params=params)
            
            if resp.status_code == 200:
                found = await parse_results_table(resp.text, rad_clean, client, demandado)
                results.extend(found)
                
                # Fallback: Si no hay nada por despacho, intentar búsqueda global por si acaso
                if not results:
                    global_search_url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search"
                    pattern_suffix = rad_clean[12:21]
                    year = pattern_suffix[:4]
                    consecutive = pattern_suffix[4:]
                    search_query = f"{year}-{consecutive}"
                    
                    print(f"[search] Fallback a búsqueda global para {search_query}")
                    resp_global = await client.get(global_search_url, params={"q": search_query})
                    if resp_global.status_code == 200:
                        found_global = await parse_results_table(resp_global.text, rad_clean, client, demandado)
                        results.extend(found_global)

    except Exception as e:
        print(f"[publicaciones.py] Error en el proceso de scraping: {e}")

    # Eliminar duplicados por source_id
    unique_results = []
    seen = set()
    for r in results:
        if r["source_id"] not in seen:
            unique_results.append(r)
            seen.add(r["source_id"])

    return unique_results

async def parse_results_table(html: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Extrae enlaces de la tabla de resultados del portal."""
    soup = BeautifulSoup(html, "html.parser")
    # Buscar filas de tabla u otros contenedores de items
    rows = soup.find_all(["tr", "li", "article", "div"], class_=re.compile(r"(row|item|card|entry)"))
    if not rows:
        rows = soup.find_all("a", href=True) # Fallback extremo

    tasks = []
    seen_urls = set()
    
    # Patrones de búsqueda
    pattern_suffix = radicado_completo[12:21]
    formatted_pattern = f"{pattern_suffix[:4]}-{pattern_suffix[4:]}"

    for row in rows:
        row_text = row.get_text()
        
        # Debe mencionar el año del radicado o el patrón para ser prometedor
        if pattern_suffix[:4] in row_text or pattern_suffix in row_text or formatted_pattern in row_text or \
           (demandado and normalize_text(demandado) in normalize_text(row_text)):
            
            links = row.find_all("a", href=True) if hasattr(row, 'find_all') else [row]
            for link in links:
                detail_url = link["href"].strip()
                if not detail_url or detail_url == "#" or detail_url.startswith("javascript:"):
                    continue
                
                if detail_url in seen_urls: continue
                seen_urls.add(detail_url)
                
                tasks.append(validate_detail_page(detail_url, radicado_completo, client, demandado))

    if not tasks: return []
    
    results = await asyncio.gather(*tasks)
    return [r for r in results if r]

async def validate_detail_page(url: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Navega al detalle para validar radicado y extraer PDF."""
    try:
        if not url.startswith("http"):
            url = "https://publicacionesprocesales.ramajudicial.gov.co" + (url if url.startswith("/") else "/" + url)
            
        try:
            resp = await client.get(url, timeout=15)
        except Exception:
            return None
            
        if resp.status_code != 200: return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = soup.get_text()
        norm_page = normalize_text(page_text)
        
        pattern_suffix = radicado_completo[12:21] 
        formatted_pattern = f"{pattern_suffix[:4]}-{pattern_suffix[4:]}"
        
        has_match = False
        if pattern_suffix in page_text or formatted_pattern in page_text or radicado_completo in page_text:
            has_match = True
        elif demandado:
            dem_norm = normalize_text(demandado)
            if dem_norm in norm_page:
                has_match = True
            
        if has_match:
            # Extraer título descriptivo
            titulo = soup.find(class_=re.compile(r"(title|header|entry-title)", re.I))
            if not titulo:
                titulo = soup.find(["h1", "h2", "h3"])
            
            titulo_text = titulo.get_text(strip=True) if titulo else "Notificación Procesal"
            if len(titulo_text) > 200: titulo_text = titulo_text[:197] + "..."
            if titulo_text.lower() in ["navegacion", "home", "search", "inicio", "enenglishesspanish"]:
                titulo_text = "Fijación/Estado Procesal"

            # Buscar el PDF
            doc_url = ""
            all_pdfs = soup.find_all("a", href=re.compile(r"(\.pdf|find_file_entry)", re.I))
            
            for pdf in all_pdfs:
                pdf_text = pdf.get_text()
                pdf_href = pdf["href"]
                if pattern_suffix in pdf_text or formatted_pattern in pdf_text or \
                   pattern_suffix in pdf_href or formatted_pattern in pdf_href:
                    doc_url = pdf_href
                    break
            
            if not doc_url and all_pdfs:
                doc_url = all_pdfs[0]["href"]
                
            if doc_url and not doc_url.startswith("http"):
                doc_url = "https://publicacionesprocesales.ramajudicial.gov.co" + (doc_url if doc_url.startswith("/") else "/" + doc_url)

            # Extraer fecha
            fecha_str = datetime.now().strftime("%Y-%m-%d")
            fecha_match = re.search(r"(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})", page_text)
            if fecha_match:
                fecha_raw = fecha_match.group(0)
                if "/" in fecha_raw:
                    try:
                        fecha_str = datetime.strptime(fecha_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                    except: pass
                else:
                    fecha_str = fecha_raw

            return {
                "fecha": fecha_str,
                "tipo": titulo_text,
                "descripcion": f"Fijación para radicado {formatted_pattern}",
                "documento_url": doc_url or url,
                "source_url": url,
                "source_id": hashlib.md5(url.encode()).hexdigest()
            }
            
    except Exception as e:
        print(f"[validate] Error: {e}")
        
    return None

def parse_fecha_pub(fecha_str: str) -> date | None:
    if not fecha_str: return None
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
    except:
        try:
            return datetime.strptime(fecha_str[:10], "%d/%m/%Y").date()
        except:
            return None

async def consultar_publicaciones(radicado: str):
    return await consultar_publicaciones_rango(radicado, datetime.now().strftime("%Y-%m-%d"))
