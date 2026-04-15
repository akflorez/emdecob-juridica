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

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

def normalize_text(text: str) -> str:
    if not text: return ""
    import unicodedata
    return "".join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn').strip()

def parse_spanish_date(date_text: str) -> str:
    """Convierte '25 de junio de 2024' a '2024-06-25'."""
    try:
        if not date_text: return datetime.now().strftime("%Y-%m-%d")
        date_text = date_text.lower().strip()
        # Limpiar palabras ruidosas
        for w in ["fijación", "fijacion", "publicado", "el ", "de "]:
            date_text = date_text.replace(w, " ").strip()
        
        # Intentar extraer día, mes (nombre) y año
        match = re.search(r"(\d+)\s+([a-z]+)\s+(\d{4})", date_text)
        if match:
            day = int(match.group(1))
            month_name = match.group(2)
            year = int(match.group(3))
            month = MESES.get(month_name, 1)
            return f"{year:04d}-{month:02d}-{day:02d}"
        
        # Fallback a ISO si ya viene algo parecido
        match_iso = re.search(r"(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})", date_text)
        if match_iso:
            raw = match_iso.group(0)
            if "/" in raw:
                return datetime.strptime(raw, "%d/%m/%Y").strftime("%Y-%m-%d")
            return raw
    except:
        pass
    return datetime.now().strftime("%Y-%m-%d")

def is_relevant_actuacion(text: str) -> bool:
    text = normalize_text(text)
    # Según instrucción del usuario: fijacion, estado o auto
    keywords = ["auto", "estado", "fijacion"]
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

    params = {
        "idDespacho": id_despacho,
        "fechaInicio": f_ini_str,
        "fechaFinal": f_fin_str,
        "action": "busqueda"
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True, verify=False) as client:
            # Primero intentar búsqueda avanzada por despacho
            resp = await client.get(SEARCH_URL, params=params)
            
            if resp.status_code == 200:
                found = await parse_results_page(resp.text, rad_clean, client, demandado)
                results.extend(found)
                
            # Fallback: Búsqueda global si no hay resultados por despacho
            if not results:
                global_search_url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search"
                pattern_suffix = rad_clean[12:21]
                year = pattern_suffix[:4]
                consecutive = pattern_suffix[4:]
                search_query = f"{year}-{consecutive}"
                
                print(f"[search] Fallback a búsqueda global para {search_query}")
                resp_global = await client.get(global_search_url, params={"q": search_query})
                if resp_global.status_code == 200:
                    found_global = await parse_results_page(resp_global.text, rad_clean, client, demandado)
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

async def parse_results_page(html: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Extrae datos directamente de los resultados de búsqueda (Search Result Cards)."""
    results = []
    soup = BeautifulSoup(html, "html.parser")
    
    # Los resultados suelen estar en elementos con clases como 'search-result' o 'list-group-item'
    cards = soup.find_all(class_=re.compile(r"(search-result|list-group-item|card|entry)", re.I))
    
    pattern_suffix = radicado_completo[12:21] 
    formatted_pattern = f"{pattern_suffix[:4]}-{pattern_suffix[4:]}"
    demandado_norm = normalize_text(demandado)

    for card in cards:
        card_text = card.get_text()
        card_norm = normalize_text(card_text)
        
        # Validar si el radicado o el demandado están presentes en este resultado
        if pattern_suffix in card_text or formatted_pattern in card_text or \
           (demandado_norm and demandado_norm in card_norm):
            
            # 1. Extraer la Fecha Real (Fijación) del tag 'label-secondary'
            # <a class="label label-lg label-secondary">25 de junio de 2024</a>
            date_tag = card.find(class_=re.compile(r"label-secondary", re.I))
            final_date = parse_spanish_date(date_tag.get_text(strip=True)) if date_tag else datetime.now().strftime("%Y-%m-%d")
            
            # 2. Extraer el Tipo/Título de los Categorías
            # <span class="asset-category">Notificaciones por Estados</span>
            categories = card.find_all(class_=re.compile(r"asset-category", re.I))
            tipo_text = "Notificación de Estado"
            potential_titles = [c.get_text(strip=True) for c in categories]
            # Priorizar nombres de notificación sobre juzgados
            for title in potential_titles:
                low = title.lower()
                if "notificacion" in low or "estado" in low or "edicto" in low:
                    tipo_text = title
                    break
            
            if not potential_titles:
                # Fallback al título del link
                link_tag = card.find("a", href=True)
                if link_tag:
                    tipo_text = link_tag.get_text(strip=True)
            
            if tipo_text.lower() in ["navegacion", "home", "search", "inicio", "enenglishesspanish"]:
                tipo_text = "Fijación Procesal"

            # 3. Direct PDF (link find_file_entry o href principal)
            doc_url = ""
            link_tag = card.find("a", href=True)
            if link_tag:
                doc_url = link_tag["href"].strip()
                if not doc_url.startswith("http"):
                    doc_url = "https://publicacionesprocesales.ramajudicial.gov.co" + (doc_url if doc_url.startswith("/") else "/" + doc_url)
            
            # Si el link no parece un archivo, intentar validarlo entrando rápido (pero solo si es necesario)
            if "find_file_entry" not in doc_url and not doc_url.lower().endswith(".pdf"):
                # Opcional: entrar al detalle solo para capturar el PDF real si el principal falla
                # Por ahora, usamos el doc_url principal que suele redirigir o ser el visor
                pass

            source_id = hashlib.md5(doc_url.encode()).hexdigest()
            
            results.append({
                "fecha": final_date,
                "tipo": tipo_text,
                "descripcion": f"Fijación para radicado {formatted_pattern}",
                "documento_url": doc_url,
                "source_url": doc_url,
                "source_id": source_id
            })

    return results

def parse_fecha_pub(fecha_str: str) -> date | None:
    if not fecha_str: return None
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
    except:
        return None

async def consultar_publicaciones(radicado: str):
    return await consultar_publicaciones_rango(radicado, datetime.now().strftime("%Y-%m-%d"))
