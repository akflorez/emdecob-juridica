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
    f_fin_str = (f_base + timedelta(days=20)).strftime("%d/%m/%Y") # 20 días naturales para cubrir rezagos

    print(f"[publicaciones.py] Buscando para radicado {radicado} en rango [{f_ini_str} - {f_fin_str}]")

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
            # 1. Intento inicial: Búsqueda específica por Despacho (basado en radicado)
            response = await client.get(BASE_URL, params=params)
            results = []
            if response.status_code == 200:
                results = await parse_results_list(response.text, radicado, client, demandado)
            
            # 2. SEGURO DE BÚSQUEDA (Broad Search): Si no hay resultados y tenemos nombre, buscamos en el Departamento
            if not results and demandado:
                print(f"(!) Sin resultados en despacho {id_despacho}. Iniciando busqueda amplia por nombre: {demandado}")
                
                # Para la búsqueda amplia usamos el endpoint de /search que es más flexible
                search_url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search"
                broad_params = {
                    "p_p_id": PORTLET_ID,
                    "p_p_lifecycle": "0",
                    "p_p_state": "normal",
                    "p_p_mode": "view",
                    f"_{PORTLET_ID}_action": "busqueda",
                    f"_{PORTLET_ID}_idDepto": id_depto,
                    f"_{PORTLET_ID}_verTotales": "true",
                    "q": demandado  # 'q' es el parámetro que usa el buscador general del portal
                }
                
                resp_broad = await client.get(search_url, params=broad_params)
                print(f"[Broad Search] Codigo de respuesta: {resp_broad.status_code}")
                if resp_broad.status_code == 200:
                    results = await parse_results_list(resp_broad.text, radicado, client, demandado)
                else:
                    print(f"[Error] Fallo busqueda amplia: Status {resp_broad.status_code}")
            
            return results

    except Exception as e:
        print(f"[Error] Error consultando publicaciones: {e}")
        return []

async def parse_results_list(html: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = "") -> list:
    """Parsea la lista inicial filtrando por palabras clave y validando el detalle."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    # Buscamos en todos los contenedores posibles donde Liferay pone resultados
    rows = soup.find_all(["tr", "li", "h4", "h5"])
    
    # Si no hay contenedores claros, tomamos todos los divs que parezcan items
    if len(rows) < 2:
        rows = soup.find_all("div", class_=re.compile(r"row|item|card|publication|search-result", re.I))
        
    # Último recurso: analizar todos los enlaces del documento
    if not rows:
        rows = soup.find_all("a", href=True)
            
    # Palabras clave flexibles
    KEYWORDS = ["notificacion", "estado", "auto", "traslado", "edicto", "fijacion", "requiere", "termino", "resolucion"]
    
    tasks = []
    seen_urls = set()

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
                detail_url = link_detalle.get("href").strip()
                if detail_url and not detail_url.startswith("#") and not detail_url.lower().startswith("javascript"):
                    # Evitar duplicados
                    if detail_url not in seen_urls:
                        seen_urls.add(detail_url)
                        
                        # OPTIMIZACIÓN: Si el link ya es un PDF y el texto tiene el radicado, es un match directo
                        rad_suffix = radicado_completo[12:21]
                        formatted_rad = f"{rad_suffix[:4]}-{rad_suffix[4:]}"
                        link_text = link_detalle.get_text()
                        
                        if ".pdf" in detail_url.lower() or ".pdf" in link_text.lower():
                            if rad_suffix in link_text or formatted_rad in link_text:
                                results.append({
                                    "fecha": datetime.now().strftime("%Y-%m-%d"), # Fecha aprox o extraer
                                    "tipo": "Publicación Directa",
                                    "descripcion": link_text.strip(),
                                    "documento_url": detail_url,
                                    "source_url": detail_url,
                                    "source_id": hashlib.md5(detail_url.encode()).hexdigest()
                                })
                            else:
                                tasks.append(validate_detail_page(detail_url, radicado_completo, client, demandado))
                        else:
                            tasks.append(validate_detail_page(detail_url, radicado_completo, client, demandado))
    
    # Ejecutar todas las validaciones en paralelo (máximo tiempo = el más lento de uno solo)
    # Limitamos a un número razonable para no saturar
    if tasks:
        all_matches = await asyncio.gather(*tasks[:15]) # Máximo 15 validaciones por actuación
        results.extend([m for m in all_matches if m])
            
    return results

async def validate_detail_page(url: str, radicado_completo: str, client: httpx.AsyncClient, demandado: str = ""):
    """Valida el patrón Año-Consecutivo (13-21) y el nombre del demandado."""
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
        elif demandado:
            dem_norm = normalize_text(demandado)
            if dem_norm in norm_page:
                print(f"✅ Match por demandado completo: {demandado} en {url}")
                has_match = True
            else:
                parts = dem_norm.split()
                if len(parts) >= 2 and parts[0] in norm_page and (parts[-1] in norm_page or parts[-2] in norm_page):
                    print(f"✅ Match por demandado parcial: {parts[0]} y apellido en {url}")
                    has_match = True
            
        if has_match:
            titulo = soup.find(["h1", "h2", "h3", "h4"])
            titulo_text = titulo.get_text(strip=True) if titulo else "Notificación de Estado"
            
            # NUEVO: Buscar el PDF ESPECÍFICO que coincide con el radicado (dígitos 13-21)
            doc_url = ""
            all_pdfs = soup.find_all("a", href=re.compile(r"\.pdf", re.I))
            
            # Primero buscamos en los enlaces de la página
            for pdf in all_pdfs:
                pdf_text = pdf.get_text()
                pdf_href = pdf["href"]
                if pattern_suffix in pdf_text or formatted_pattern in pdf_text or \
                   pattern_suffix in pdf_href or formatted_pattern in pdf_href:
                    doc_url = pdf_href
                    print(f"✅ PDF específico encontrado: {pdf_text[:50]}")
                    break
            
            # Si no hay match específico, tomamos el primer PDF que encontremos (fallback)
            if not doc_url and all_pdfs:
                doc_url = all_pdfs[0]["href"]
                
            if doc_url and doc_url.startswith("/"):
                doc_url = "https://publicacionesprocesales.ramajudicial.gov.co" + doc_url

            fecha_str = datetime.now().strftime("%Y-%m-%d")
            # Buscar fecha en la página
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
    """Mantiene compatibilidad con el llamado básico."""
    return await consultar_publicaciones_rango(radicado)
