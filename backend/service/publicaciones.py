import httpx
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime, timedelta
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
    return "fijacion estado" in norm or "auto" in norm

async def consultar_publicaciones_rango(radicado: str, fecha_inicio: str = None, fecha_fin: str = None):
    """
    Busca publicaciones para un radicado en un rango de fechas.
    fecha_inicio/fin en formato DD/MM/YYYY
    """
    if not radicado or len(radicado) < 12:
        return []

    id_despacho = radicado[:12]
    
    # Si no se pasan fechas, el portal suele fallar o traer demasiado
    today_str = datetime.now().strftime("%d/%m/%Y")
    f_ini = fecha_inicio or today_str
    f_fin = fecha_fin or today_str

    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": "+",
        f"_{PORTLET_ID}_idDespacho": id_despacho,
        f"_{PORTLET_ID}_fechaInicio": f_ini,
        f"_{PORTLET_ID}_fechaFin": f_fin,
        f"_{PORTLET_ID}_verTotales": "true",
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            response = await client.get(BASE_URL, params=params)
            if response.status_code != 200:
                print(f"⚠️ Error en portal publicaciones: {response.status_code}")
                return []
            
            return await parse_results_list(response.text, radicado, client)

    except Exception as e:
        print(f"💥 Error consultando publicaciones: {e}")
        return []

async def parse_results_list(html: str, radicado_completo: str, client: httpx.AsyncClient) -> list:
    """Parsea la lista inicial y entra en detalles si hay posibles matches."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    # En el nuevo portal, las publicaciones son bloques con clase que contiene la info
    # Según el screenshot, hay botones 'VER DETALLE'
    links_detalle = soup.find_all("a", string=re.compile("VER DETALLE", re.I))
    
    for link in links_detalle:
        detail_url = link.get("href")
        if not detail_url: continue
        
        # Debemos entrar al detalle para validar radicado/nombres
        match = await validate_detail_page(detail_url, radicado_completo, client)
        if match:
            results.append(match)
            
    return results

async def validate_detail_page(url: str, radicado_completo: str, client: httpx.AsyncClient):
    """Entra a la página de detalle y valida si el proceso está ahí."""
    try:
        if url.startswith("/"):
            url = "https://publicacionesprocesales.ramajudicial.gov.co" + url
            
        resp = await client.get(url)
        if resp.status_code != 200: return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = soup.get_text()
        
        # Validación 1: El radicado completo o los últimos 9 dígitos
        last_9 = radicado_completo[-9:]
        if radicado_completo in page_text or last_9 in page_text:
            titulo = soup.find(["h1", "h2", "h3", "h4"])
            titulo_text = titulo.get_text(strip=True) if titulo else "Notificación Procesal"
            
            doc_link = soup.find("a", href=re.compile(r"\.pdf", re.I))
            doc_url = doc_link["href"] if doc_link else ""
            if doc_url and doc_url.startswith("/"):
                doc_url = "https://publicacionesprocesales.ramajudicial.gov.co" + doc_url

            fecha_str = datetime.now().strftime("%Y-%m-%d") # Fallback
            fecha_match = re.search(r"(\d{4}-\d{2}-\d{2})", page_text)
            if fecha_match:
                fecha_str = fecha_match.group(1)

            return {
                "fecha": fecha_str,
                "tipo": titulo_text,
                "descripcion": "Encontrado en Publicaciones Procesales por radicado.",
                "url_documento": doc_url or url,
                "source_url": url,
                "source_id": hashlib.md5(url.encode()).hexdigest()
            }
            
    except Exception as e:
        print(f"⚠️ Error validando detalle: {e}")
        
    return None

def parse_fecha_pub(fecha_str: str) -> datetime.date | None:
    if not fecha_str: return None
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
    except:
        try:
            return datetime.strptime(fecha_str[:10], "%d/%m/%Y").date()
        except:
            return None

# Retrocompatibilidad con el nombre anterior
async def consultar_publicaciones(radicado: str):
    return await consultar_publicaciones_rango(radicado)
