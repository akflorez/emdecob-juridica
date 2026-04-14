import httpx
import asyncio
from bs4 import BeautifulSoup
import re
from datetime import datetime, date, timedelta
import hashlib
from typing import List, Dict, Optional

# Configuración
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales"
PORTLET_ID = "p_p_id_visualizacion_publicaciones_WAR_publicacionesprocesalesportlet"

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
    keywords = ["auto", "notificacion", "estado", "traslado", "termino", "requiere", "despacho"]
    return any(k in text for k in keywords)

async def consultar_publicaciones_rango(radicado_completo: str, fecha_act_str: str, demandado: str = ""):
    """
    Busca publicaciones en el portal de la Rama Judicial en una ventana de tiempo.
    Utiliza 3 estrategias paralelas: Radicado exacto, Búsqueda 'q' con radicado y Búsqueda amplia por nombre.
    """
    results = []
    if not radicado_completo or len(radicado_completo.strip()) < 12:
        return []

    # Limpiar radicado (quitar espacios)
    rad_clean = radicado_completo.strip().replace(" ", "")
    
    # Rango de fechas: Desde la fecha de actuación hasta 20 días después
    try:
        f_base = datetime.strptime(fecha_act_str, "%Y-%m-%d")
    except:
        f_base = datetime.now() - timedelta(days=5)

    f_ini_str = f_base.strftime("%d/%m/%Y")
    f_fin_str = (f_base + timedelta(days=20)).strftime("%d/%m/%Y")

    print(f"🔍 [publicaciones.py] Buscando para radicado {rad_clean} en rango [{f_ini_str} - {f_fin_str}]")

    search_url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search"

    common_params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "2",
        "p_p_state": "normal",
        "p_p_mode": "view",
        "p_p_resource_id": "consultarPublicaciones",
        "p_p_cacheability": "cacheLevelPage",
        "p_p_col_id": "column-1",
        "p_p_col_count": "1",
        "fechaInicial": f_ini_str,
        "fechaFinal": f_fin_str,
    }

    # Búsqueda 1: Por radicado exacto
    params1 = common_params.copy()
    params1["radicado"] = rad_clean

    # Búsqueda 2: General 'q' con radicado
    params2 = common_params.copy()
    params2["q"] = rad_clean

    # Búsqueda 3: General 'q' con nombre (si existe)
    search_tasks = [params1, params2]
    if demandado:
        params3 = common_params.copy()
        params3["q"] = demandado
        search_tasks.append(params3)

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True, verify=False) as client:
            http_tasks = [client.get(search_url, params=p) for p in search_tasks]
            responses = await asyncio.gather(*http_tasks, return_exceptions=True)
            
            for resp in responses:
                if isinstance(resp, httpx.Response) and resp.status_code == 200:
                    found = await parse_results_list(resp.text, rad_clean, client, demandado)
                    results.extend(found)
                    
    except Exception as e:
        print(f"💥 Error en el proceso de scraping: {e}")

    # Eliminar duplicados por source_id
    unique_results = []
    seen = set()
    for r in results:
        if r["source_id"] not in seen:
            unique_results.append(r)
            seen.add(r["source_id"])

    return unique_results

async def parse_results_list(html: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Extrae enlaces de interés de la página de resultados."""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    if not rows:
        rows = soup.find_all("li", class_="list-group-item") or soup.find_all("div", class_="row")
    
    if not rows:
        # Fallback agresivo: buscar cualquier link que parezca una publicación
        rows = soup.find_all("a", href=True)
            
    KEYWORDS = ["notificacion", "estado", "auto", "traslado", "edicto", "fijacion", "requiere", "termino", "resolucion"]
    
    tasks = []
    seen_urls = set()

    for row in rows:
        row_text = row.get_text()
        norm_text = normalize_text(row_text)
        
        # Debe tener alguna palabra clave
        if any(k in norm_text for k in KEYWORDS):
            link = row.find("a", href=True) if hasattr(row, 'find') else row
            if not link or not link.has_attr('href'): continue
            
            detail_url = link["href"]
            if detail_url in seen_urls: continue
            seen_urls.add(detail_url)
            
            tasks.append(validate_detail_page(detail_url, radicado_completo, client, demandado))

    if not tasks: return []
    
    results = await asyncio.gather(*tasks)
    return [r for r in results if r]

async def validate_detail_page(url: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Valida si en la página de detalle está el PDF del radicado (Dígitos 13-21)."""
    try:
        url = url.strip()
        if not url.startswith("http"):
            if url.startswith("/"):
                url = "https://publicacionesprocesales.ramajudicial.gov.co" + url
            else:
                return None
            
        resp = await client.get(url)
        if resp.status_code != 200: return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = soup.get_text()
        norm_page = normalize_text(page_text)
        
        # Patrón Año-Consecutivo: dígitos 13 al 21
        # Ejemplo: 110014189027 2024 01322 00 -> 2024-01322
        pattern_suffix = radicado_completo[12:21] 
        year = pattern_suffix[:4]
        consecutive = pattern_suffix[4:]
        formatted_pattern = f"{year}-{consecutive}"
        
        has_match = False
        if pattern_suffix in page_text or formatted_pattern in page_text:
            has_match = True
        elif demandado:
            dem_norm = normalize_text(demandado)
            if dem_norm in norm_page:
                has_match = True
            else:
                parts = dem_norm.split()
                if len(parts) >= 2 and parts[0] in norm_page and (parts[-1] in norm_page or parts[-2] in norm_page):
                    has_match = True
            
        if has_match:
            titulo = soup.find(["h1", "h2", "h3", "h4"])
            titulo_text = titulo.get_text(strip=True) if titulo else "Notificación de Estado"
            
            # Buscar el PDF ESPECÍFICO (Año-Consecutivo)
            doc_url = ""
            all_pdfs = soup.find_all("a", href=re.compile(r"\.pdf", re.I))
            
            for pdf in all_pdfs:
                pdf_text = pdf.get_text()
                pdf_href = pdf["href"]
                if pattern_suffix in pdf_text or formatted_pattern in pdf_text or \
                   pattern_suffix in pdf_href or formatted_pattern in pdf_href:
                    doc_url = pdf_href
                    break
            
            if not doc_url and all_pdfs:
                doc_url = all_pdfs[0]["href"]
                
            if doc_url and doc_url.startswith("/"):
                doc_url = "https://publicacionesprocesales.ramajudicial.gov.co" + doc_url

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
        print(f"⚠️ Error validando detalle: {e}")
        
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
