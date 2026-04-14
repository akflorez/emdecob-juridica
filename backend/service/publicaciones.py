import httpx
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime, timedelta, date
import re
import unicodedata
import hashlib

# El portal de Publicaciones Procesales es sensible a la estructura de Liferay
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"
PORTLET_ID = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

def normalize_text(text: str) -> str:
    """Quita tildes y pone en minúsculas para comparaciones robustas."""
    if not text: return ""
    text = text.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

def is_relevant_actuacion(descripcion: str) -> bool:
    """Valida si la actuación debe disparar una búsqueda en Publicaciones."""
    norm = normalize_text(descripcion)
    # Según audio: "si hay una actuación que diga fijación de estado o que diga auto"
    return "fijacion estado" in norm or "auto" in norm

async def consultar_publicaciones_rango(radicado: str, fecha_actuacion: str = None, demandado: str = ""):
    """
    Busca publicaciones para un radicado basándose en la fecha de la actuación.
    Siguiendo las instrucciones del usuario:
    - Despacho: primeros 12 dígitos.
    - Rango: [Fecha Actuación, Fecha Actuación + 7 días].
    - Filtro: Palabras clave "Notificación" o "Estado".
    - Validar: Patrón Año-Consecutivo (dígitos 13-21) en el PDF o contenido.
    """
    if not radicado or len(radicado) < 12:
        return []

    id_depto = radicado[:2]
    id_despacho = radicado[:12]
    
    # Rango de 7 días porque a veces la publicación ocurre días después
    try:
        if isinstance(fecha_actuacion, str):
            f_base = datetime.strptime(fecha_actuacion[:10], "%Y-%m-%d")
        elif isinstance(fecha_actuacion, (date, datetime)):
            f_base = datetime.combine(fecha_actuacion, datetime.min.time())
        else:
            f_base = datetime.now()
    except:
        f_base = datetime.now()

    f_ini_str = f_base.strftime("%d/%m/%Y")
    f_fin_str = (f_base + timedelta(days=7)).strftime("%d/%m/%Y")

    print(f"🔍 [publicaciones.py] Buscando para radicado {radicado} en rango [{f_ini_str} - {f_fin_str}]")

    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": id_depto,
        f"_{PORTLET_ID}_idDespacho": id_despacho,
        f"_{PORTLET_ID}_fechaInicio": f_ini_str,
        f"_{PORTLET_ID}_fechaFin": f_fin_str,
        f"_{PORTLET_ID}_verTotales": "true",
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True, verify=False) as client:
            response = await client.get(BASE_URL, params=params)
            if response.status_code != 200:
                print(f"⚠️ Error en portal publicaciones: {response.status_code}")
                return []
            
            return await parse_results_list(response.text, radicado, client, demandado)

    except Exception as e:
        print(f"💥 Error consultando publicaciones: {e}")
        return []

async def parse_results_list(html: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = "") -> list:
    """Parsea la lista inicial filtrando por palabras clave y validando el detalle."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    rows = soup.find_all("tr")
    if not rows:
        rows = soup.find_all("div", class_=re.compile(r"row|item|card", re.I))

    # Palabras clave flexibles según audio: "vayan filtrando si por el nombre notificación o por el nombre estado"
    KEYWORDS = ["notificacion", "estado"]

    for row in rows:
        row_text = row.get_text()
        norm_row = normalize_text(row_text)
        
        # Filtro: Contiene alguna palabra clave
        is_relevant = any(k in norm_row for k in KEYWORDS)
        
        if is_relevant:
            # Encontrar el enlace de detalle
            link_detalle = row.find("a", string=re.compile(r"VER DETALLE|ACCEDER|VER", re.I))
            if not link_detalle:
                link_detalle = row.find("a", href=True)
            
            if link_detalle and link_detalle.get("href"):
                detail_url = link_detalle.get("href")
                match = await validate_detail_page(detail_url, radicado_completo, client, demandado)
                if match:
                    results.append(match)
            
    return results

async def validate_detail_page(url: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Valida el patrón Año-Consecutivo (13-21) y el nombre del demandado."""
    try:
        if url.startswith("/"):
            url = "https://publicacionesprocesales.ramajudicial.gov.co" + url
            
        resp = await client.get(url)
        if resp.status_code != 200: return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = soup.get_text()
        norm_page = normalize_text(page_text)
        
        # Patrón Año-Consecutivo: dígitos 13 al 21 (9 dígitos en total)
        # Ejemplo: 11001418902720250010600 -> Año 2025, Consecutivo 00106
        # index 12 to 21
        pattern_suffix = radicado_completo[12:21] 
        year = pattern_suffix[:4]
        consecutive = pattern_suffix[4:]
        formatted_pattern = f"{year}-{consecutive}"
        
        has_match = False
        if pattern_suffix in page_text or formatted_pattern in page_text:
            print(f"✅ Match por radicado: {formatted_pattern} en {url}")
            has_match = True
        elif demandado and normalize_text(demandado) in norm_page:
            print(f"✅ Match por demandado: {demandado} en {url}")
            has_match = True
            
        if has_match:
            titulo = soup.find(["h1", "h2", "h3", "h4"])
            titulo_text = titulo.get_text(strip=True) if titulo else "Notificación de Estado"
            
            # Buscar el link del PDF
            doc_link = soup.find("a", href=re.compile(r"\.pdf", re.I))
            doc_url = doc_link["href"] if doc_link else ""
            if doc_url and doc_url.startswith("/"):
                doc_url = "https://publicacionesprocesales.ramajudicial.gov.co" + doc_url

            fecha_str = datetime.now().strftime("%Y-%m-%d")
            # Buscar fecha
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
                "descripcion": f"Fijación encontrada para radicado ...{pattern_suffix}",
                "url_documento": doc_url or url,
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
    """Mantiene compatibilidad con el llamado básico."""
    return await consultar_publicaciones_rango(radicado)
