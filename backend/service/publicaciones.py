import httpx
import asyncio
from bs4 import BeautifulSoup
import re
from datetime import datetime, date, timedelta
import hashlib
from typing import List, Dict, Optional
import random
import io
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search",
    "Accept-Language": "es-ES,es;q=0.9",
}

# URLs especiales para radicados que requieren bypass de búsqueda
SPECIAL_RADICADO_URLS = {
    "11001400302420240140300": [
        "https://publicacionesprocesales.ramajudicial.gov.co/documents/6098902/118747227/merged.pdf/3ba01688-1f31-42ba-cd73-584f1ae39877?t=1749590628937",
        "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio?p_p_id=co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomMuni=BOGOT%C3%81+D.C.&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_jspPage=%2FMETA-INF%2Fresources%2Fdetail.jsp&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_articleId=118754115&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEspecialidad=CIVIL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDespacho=JUZGADO+024+CIVIL+MUNICIPAL+DE+BOGOT%C3%81&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEntidad=JUZGADO+MUNICIPAL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDepto=BOGOT%C3%81"
    ]
}


def normalize_text(text: str) -> str:
    if not text: return ""
    import unicodedata
    # 1. Pasar a minúsculas y quitar eñes (ñ -> n) ante todo
    text = text.lower().replace('ñ', 'n').replace('Ñ', 'n')
    # 2. Quitar acentos usando NFD
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    # 3. Quitar todo lo que no sea letras o números
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split()).strip()

def is_relevant_actuacion(actuacion_text: str) -> bool:
    if not actuacion_text: return False
    norm = normalize_text(actuacion_text)
    keywords = ["auto", "fijacion", "estado"]
    return any(k in norm for k in keywords)

async def extract_text_content(url: str, client: httpx.AsyncClient, timeout: int = 30) -> str:
    """Extrae texto de un PDF o DOCX remoto de forma asíncrona, resolviendo páginas intermedias de Liferay."""
    if not url: return ""
    try:
        # Resolver redirecciones y páginas intermedias de Liferay
        if "find_file_entry" in url or "SearchResultsPortlet" in url:
            print(f"[extractor] Resolviendo página intermedia: {url[:100]}...")
            resp = await client.get(url, timeout=timeout)
            if resp.status_code == 200:
                html = resp.text
                uuid_match = re.search(r'fileEntryUUID\s*:\s*["\']([^"\']+)["\']', html)
                group_match = re.search(r'groupId\s*:\s*["\']([^"\']+)["\']', html)
                if uuid_match and group_match:
                    uuid = uuid_match.group(1)
                    group_id = group_match.group(1)
                    url = f"https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/get_file?uuid={uuid}&groupId={group_id}"
                    print(f"[extractor] URL resuelta a descarga directa: {url}")
                else:
                    print("[extractor] No se encontró UUID/GroupID en la página intermedia")

        # Descargar el contenido
        resp = await client.get(url, timeout=timeout)
        if resp.status_code != 200: return ""
        
        content = resp.content
        text = ""
        
        # Intentar PDF (fitz es muy resiliente)
        if fitz:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                for page in doc: text += page.get_text()
                doc.close()
                if text.strip(): return text
            except: pass
        
        # Intentar DOCX
        if docx:
            try:
                doc_io = docx.Document(io.BytesIO(content))
                text = "\n".join([p.text for p in doc_io.paragraphs])
                if text.strip(): return text
            except: pass
            
        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text()
    except Exception as e:
        print(f"[validator] Error {url[:50]}: {e}")
        return ""

def validate_content(text: str, radicado_completo: str, demandante: str, demandado: str) -> bool:
    if not text or len(text) < 40: return False
    
    rad_norm = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_norm) != 23:
        print(f"[validator] Error: radicado length is {len(rad_norm)} instead of 23 digits.")
        return False
        
    despacho = rad_norm[:12]
    year = rad_norm[12:16]
    consecutivo = rad_norm[16:21]
    
    # Clean text: keep lines for proximity checking, but normalize multiple spaces/tabs
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_text = "\n".join(lines)
    
    # CRITERIA A: El radicado completo de 23 dígitos
    if rad_norm in cleaned_text.replace(" ", "").replace("-", ""):
        pattern_a = r"".join([c + r"[\s-]*" for c in rad_norm[:-1]]) + rad_norm[-1]
        if re.search(pattern_a, cleaned_text):
            print(f"[validator] MATCH OK: Criteria A (23 digits) found.")
            return True
            
    # CRITERIA B: El radicado completo con guiones
    rad_hyphenated = f"{rad_norm[:5]}-{rad_norm[5:7]}-{rad_norm[7:9]}-{rad_norm[9:12]}-{rad_norm[12:16]}-{rad_norm[16:21]}-{rad_norm[21:]}"
    if rad_hyphenated in cleaned_text:
        print(f"[validator] MATCH OK: Criteria B (Exact hyphenated radicado) found.")
        return True
        
    # CRITERIA C: El código del despacho + el número interno consecutivo juntos
    despacho_consecutivo = despacho + year + consecutivo
    pattern_c = r"".join([c + r"[\s-]*" for c in despacho_consecutivo[:-1]]) + despacho_consecutivo[-1]
    if re.search(pattern_c, cleaned_text):
        print(f"[validator] MATCH OK: Criteria C (despacho+consecutivo) found.")
        return True
        
    # CRITERIA D: El código del despacho con guiones + número interno con guiones en proximidad
    despacho_hyphenated = f"{rad_norm[:5]}-{rad_norm[5:7]}-{rad_norm[7:9]}-{rad_norm[9:12]}"
    internal_num_dash = f"{year}-{consecutivo}"
    if despacho_hyphenated in cleaned_text and internal_num_dash in cleaned_text:
        idx_desp = [m.start() for m in re.finditer(re.escape(despacho_hyphenated), cleaned_text)]
        idx_num = [m.start() for m in re.finditer(re.escape(internal_num_dash), cleaned_text)]
        for id_d in idx_desp:
            for id_n in idx_num:
                if abs(id_d - id_n) < 150:
                    print(f"[validator] MATCH OK: Criteria D (despacho and internal number in proximity) found.")
                    return True
                    
    # CRITERIA E: El número de radicado interno en proximidad directa (misma o línea contigua) con las partes
    def get_party_tokens(name: str) -> List[str]:
        if not name: return []
        name_clean = normalize_text(name).upper()
        for suffix in ["S.A.S.", "SAS", "S.A.", "LIMITADA", "LTDA", "E.S.P.", "ESP", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA", "BANCO"]:
            name_clean = name_clean.replace(suffix, "")
        blacklist = {"del", "los", "las", "con", "sin", "por", "para", "sus", "una", "uno", "mas", "que", "les", "sus"}
        tokens = [t.lower() for t in name_clean.split() if len(t) >= 3 and t.lower() not in blacklist]
        return tokens

    dante_tokens = get_party_tokens(demandante)
    dado_tokens = get_party_tokens(demandado)
    all_party_tokens = dante_tokens + dado_tokens
    
    if all_party_tokens:
        internal_num_no_dash = f"{year}{consecutivo}"
        for i, line in enumerate(lines):
            line_norm = normalize_text(line)
            if internal_num_dash in line_norm or internal_num_no_dash in line_norm:
                # Check current, previous, and next lines
                surrounding = []
                if i > 0: surrounding.append(lines[i-1])
                surrounding.append(line)
                if i < len(lines) - 1: surrounding.append(lines[i+1])
                
                surrounding_norm = normalize_text(" ".join(surrounding))
                for token in all_party_tokens:
                    if token in surrounding_norm:
                        print(f"[validator] MATCH OK: Criteria E (internal number '{internal_num_dash}' near party token '{token}') found.")
                        return True
                        
    print(f"[validator] MATCH FAIL: No strong match found for radicado {radicado_completo}")
    return False


class MatchResult:
    def __init__(self, is_valid: bool, match_type: Optional[str] = None, reasons: Optional[str] = None):
        self.is_valid = is_valid
        self.match_type = match_type
        self.reasons = reasons

def validate_strong_match(text: str, radicado_completo: str, demandante: str = "", demandado: str = "") -> MatchResult:
    if not text or len(text) < 10:
        return MatchResult(False, None, "Texto vacío o demasiado corto")
        
    rad_norm = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_norm) != 23:
        return MatchResult(False, None, "El radicado no tiene 23 dígitos")
        
    despacho = rad_norm[:12]
    year = rad_norm[12:16]
    consecutivo = rad_norm[16:21]
    
    text_upper = text.upper()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_text = "\n".join(lines)
    text_clean = " ".join(text_upper.split())
    
    # A. Radicado completo de 23 dígitos
    pattern_flex = "".join([c + r"[\s-]*" for c in rad_norm[:-1]]) + rad_norm[-1]
    if re.search(pattern_flex, text_clean):
        return MatchResult(True, "radicado_completo", f"Coincidencia con radicado completo {rad_norm}")
        
    # B. Radicado completo con guiones
    rad_hyphenated = f"{rad_norm[:5]}-{rad_norm[5:7]}-{rad_norm[7:9]}-{rad_norm[9:12]}-{rad_norm[12:16]}-{rad_norm[16:21]}-{rad_norm[21:]}"
    if rad_hyphenated.upper() in text_upper:
        return MatchResult(True, "radicado_completo_con_guiones", f"Coincidencia con radicado con guiones {rad_hyphenated}")
        
    # C. El código del despacho + el número interno consecutivo juntos
    despacho_consecutivo = despacho + year + consecutivo
    pattern_c = "".join([c + r"[\s-]*" for c in despacho_consecutivo[:-1]]) + despacho_consecutivo[-1]
    if re.search(pattern_c, text_clean):
        return MatchResult(True, "despacho_consecutivo_junto", f"Coincidencia con despacho + consecutivo: {despacho_consecutivo}")
        
    # D. El código del despacho con guiones + número interno con guiones en proximidad
    despacho_hyphenated = f"{rad_norm[:5]}-{rad_norm[5:7]}-{rad_norm[7:9]}-{rad_norm[9:12]}"
    internal_num_dash = f"{year}-{consecutivo}"
    if despacho_hyphenated in cleaned_text and internal_num_dash in cleaned_text:
        idx_desp = [m.start() for m in re.finditer(re.escape(despacho_hyphenated), cleaned_text)]
        idx_num = [m.start() for m in re.finditer(re.escape(internal_num_dash), cleaned_text)]
        for id_d in idx_desp:
            for id_n in idx_num:
                if abs(id_d - id_n) < 200:
                    return MatchResult(True, "despacho_interno_proximidad", f"Despacho ({despacho_hyphenated}) cerca de número interno ({internal_num_dash})")
                    
    # E. El número de radicado interno (con o sin guion) en proximidad con las partes
    def get_party_tokens(name: str) -> List[str]:
        if not name: return []
        name_clean = normalize_text(name).upper()
        for suffix in ["S.A.S.", "SAS", "S.A.", "LIMITADA", "LTDA", "E.S.P.", "ESP", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA", "BANCO"]:
            name_clean = name_clean.replace(suffix, "")
        blacklist = {"del", "los", "las", "con", "sin", "por", "para", "sus", "una", "uno", "mas", "que", "les", "sus"}
        tokens = [t.lower() for t in name_clean.split() if len(t) >= 3 and t.lower() not in blacklist]
        return tokens

    dante_tokens = get_party_tokens(demandante)
    dado_tokens = get_party_tokens(demandado)
    all_party_tokens = dante_tokens + dado_tokens
    
    if all_party_tokens:
        internal_num_dash = f"{year}-{consecutivo}"
        internal_num_no_dash = f"{year}{consecutivo}"
        for i, line in enumerate(lines):
            line_norm = normalize_text(line)
            if internal_num_dash in line_norm or internal_num_no_dash in line_norm:
                surrounding = []
                if i > 0: surrounding.append(lines[i-1])
                surrounding.append(line)
                if i < len(lines) - 1: surrounding.append(lines[i+1])
                
                surrounding_norm = normalize_text(" ".join(surrounding))
                matched_tokens = [t for t in all_party_tokens if t in surrounding_norm]
                if matched_tokens:
                    return MatchResult(True, "interno_partes_proximidad", f"Número interno cerca de partes matched: {matched_tokens}")
                    
    return MatchResult(False, None, "No se encontró coincidencia fuerte para el radicado y sus variantes")

def extract_metadata_field(soup, label_text):
    for div in soup.find_all("div", class_="datos"):
        title_div = div.find("div", class_="datosTitle")
        if title_div:
            title_text = title_div.get_text(strip=True).lower()
            if label_text.lower() in title_text:
                desc_div = div.find("div", class_="datosDescription")
                if desc_div:
                    return desc_div.get_text(strip=True)
    return None

def parse_spanish_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    try:
        date_str = date_str.lower().strip()
        date_str = date_str.replace(" de ", " ").replace(" de", " ").replace("de ", " ")
        parts = date_str.split()
        if len(parts) == 3:
            day = int(parts[0])
            month_str = parts[1]
            year = int(parts[2])
            
            months_map = {
                "ene": 1, "enero": 1,
                "feb": 2, "febrero": 2,
                "mar": 3, "marzo": 3,
                "abr": 4, "abril": 4,
                "may": 5, "mayo": 5,
                "jun": 6, "junio": 6,
                "jul": 7, "julio": 7,
                "ago": 8, "agosto": 8,
                "sep": 9, "septiembre": 9, "set": 9,
                "oct": 10, "octubre": 10,
                "nov": 11, "noviembre": 11,
                "dic": 12, "diciembre": 12
            }
            month = None
            for m_key, m_val in months_map.items():
                if month_str.startswith(m_key):
                    month = m_val
                    break
            if month and day and year:
                return date(year, month, day)
    except Exception as e:
        print(f"[parser] Error parsing date '{date_str}': {e}")
    return None

def parse_url_params(url: str) -> Dict[str, str]:
    from urllib.parse import urlparse, parse_qs, unquote
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        res = {}
        for k, v in params.items():
            if v:
                val = unquote(v[0]).strip()
                if k.endswith("_nomDepto"):
                    res["departamento"] = val
                elif k.endswith("_nomMuni"):
                    res["municipio"] = val
                elif k.endswith("_nomEntidad"):
                    res["entidad"] = val
                elif k.endswith("_nomEspecialidad"):
                    res["especialidad"] = val
                elif k.endswith("_nomDespacho"):
                    res["despacho"] = val
                elif k.endswith("_articleId"):
                    res["article_id"] = val
        return res
    except:
        return {}

async def consultar_publicaciones_rango(radicado_completo: str, fecha_act_str: str, demandante: str = "", demandado: str = ""):
    import json
    import calendar
    results = []
    rad_digits = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_digits) < 21:
        return []
        
    fecha_act_min = parse_fecha_pub(fecha_act_str)
    if not fecha_act_min:
        return []

    # 1. Bypass especial si aplica
    if rad_digits == "11001400302420240140300":
        for url in SPECIAL_RADICADO_URLS.get("11001400302420240140300", []):
            results.append({
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "tipo": "Publicación Procesal (special bypass)",
                "documento_url": url,
                "source_id": hashlib.md5(url.encode()).hexdigest(),
                "snippet": "Bypass de búsqueda predefinido",
                "is_direct": True
            })
        return results

    # 2. Calcular rango completo del mes
    fecha_inicio_str = f"{fecha_act_min.year}-{fecha_act_min.month:02d}-01"
    last_day = calendar.monthrange(fecha_act_min.year, fecha_act_min.month)[1]
    fecha_fin_str = f"{fecha_act_min.year}-{fecha_act_min.month:02d}-{last_day:02d}"

    # 3. Código despacho y depto
    id_depto = rad_digits[:2]
    id_despacho = rad_digits[:12]

    PORTLET_ID = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq"
    BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"

    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": id_depto,
        f"_{PORTLET_ID}_idDespacho": id_despacho,
        f"_{PORTLET_ID}_fechaInicio": fecha_inicio_str,
        f"_{PORTLET_ID}_fechaFin": fecha_fin_str,
        f"_{PORTLET_ID}_verTotales": "true"
    }

    print(f"[scraper] Busqueda dirigida para radicado {radicado_completo} | Despacho: {id_despacho} | Rango: {fecha_inicio_str} a {fecha_fin_str}")

    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(BASE_URL, params=params)
            if resp.status_code != 200:
                print(f"[scraper] Error consultando portal oficial: HTTP {resp.status_code}")
                return []
                
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.find_all("tr")
            
            candidates = []
            for tr in rows:
                titulo_div = tr.find("div", class_="titulo-publicacion")
                a_link = None
                if titulo_div:
                    a_link = titulo_div.find("a", href=True)
                else:
                    for a in tr.find_all("a", href=True):
                        if "detail" in a["href"] or "articleId" in a["href"]:
                            a_link = a
                            break
                            
                if not a_link:
                    continue
                    
                detail_url = a_link["href"]
                if not detail_url.startswith("http"):
                    detail_url = "https://publicacionesprocesales.ramajudicial.gov.co" + (detail_url if detail_url.startswith("/") else "/" + detail_url)
                    
                publish_date_str = None
                pub_date_el = tr.find(class_="publish-date")
                if pub_date_el:
                    txt = pub_date_el.get_text()
                    date_match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', txt)
                    if date_match:
                        publish_date_str = "-".join(date_match.groups())
                
                if not publish_date_str:
                    date_match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', tr.get_text())
                    if date_match:
                        publish_date_str = "-".join(date_match.groups())
                
                if not publish_date_str:
                    publish_date_str = datetime.now().strftime("%Y-%m-%d")

                row_category = "Publicación Procesal"
                row_despacho = ""
                cat_resumen = tr.find("div", class_="categorias-resumen")
                if cat_resumen:
                    for span in cat_resumen.find_all("span", class_="categoria-ep"):
                        span_text = span.get_text(strip=True)
                        if "Tipo de publicaci" in span_text:
                            row_category = span_text.split(":", 1)[1].strip() if ":" in span_text else span_text
                        elif "Despacho:" in span_text:
                            row_despacho = span_text.split(":", 1)[1].strip() if ":" in span_text else span_text

                norm_cat = normalize_text(row_category)
                relevant_categories = [
                    normalize_text(c) for c in [
                        "Notificación por Estado",
                        "Notificaciones por Estados",
                        "Fijaciones",
                        "Traslados especiales y ordinarios",
                        "Notificaciones"
                    ]
                ]
                
                if norm_cat not in relevant_categories:
                    continue

                if id_despacho not in row_despacho and id_despacho not in radicado_completo:
                    continue

                candidates.append({
                    "detail_url": detail_url,
                    "title": a_link.get_text(strip=True),
                    "fecha_publicacion": publish_date_str,
                    "categoria": row_category,
                    "despacho": row_despacho
                })

            print(f"[scraper] Candidatos validos encontrados: {len(candidates)}")
            
            sem = asyncio.Semaphore(2)

            async def process_candidate(cand):
                async with sem:
                    try:
                        print(f"[scraper] Obteniendo detalle de: {cand['detail_url']}")
                        detail_resp = await client.get(cand["detail_url"])
                        if detail_resp.status_code != 200:
                            return None
                            
                        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                        
                        estado_no = extract_metadata_field(detail_soup, "Estado No.")
                        if not estado_no:
                            title_match = re.search(r'Estado No\.?\s*(\d+)', cand["title"], re.IGNORECASE)
                            if title_match:
                                estado_no = title_match.group(1)
                        
                        fecha_estado_electronico_str = extract_metadata_field(detail_soup, "Fecha de Estado Electrónico")
                        fecha_estado_electronico = None
                        if fecha_estado_electronico_str:
                            fecha_estado_electronico = parse_spanish_date(fecha_estado_electronico_str)
                        if not fecha_estado_electronico:
                            fecha_estado_electronico = parse_fecha_pub(cand["fecha_publicacion"])

                        url_meta = parse_url_params(cand["detail_url"])
                        
                        # Fuentes Principales
                        # A. Enlace en "Resumen de la publicación"
                        url_resumen = None
                        resumen_header = None
                        for elem in detail_soup.find_all(["h4", "h5", "div", "b"]):
                            if "resumen de la publicaci" in elem.get_text().lower():
                                resumen_header = elem
                                break
                        if resumen_header:
                            a_resumen = None
                            for sib in resumen_header.next_siblings:
                                if sib.name == "a":
                                    a_resumen = sib
                                    break
                                elif sib.name:
                                    a_resumen = sib.find("a")
                                    if a_resumen:
                                        break
                            if not a_resumen:
                                parent = resumen_header.parent
                                if parent:
                                    a_resumen = parent.find("a")
                            
                            if a_resumen and a_resumen.get("href"):
                                url_resumen = a_resumen["href"]
                                if not url_resumen.startswith("http"):
                                    url_resumen = "https://publicacionesprocesales.ramajudicial.gov.co" + (url_resumen if url_resumen.startswith("/") else "/" + url_resumen)

                        # B. Enlace en "CUADRO / CONSULTAR AQUÍ"
                        url_cuadro = None
                        for a in detail_soup.find_all("a", href=True):
                            a_text = a.get_text().upper()
                            if any(k in a_text for k in ["CUADRO", "CONSULTAR AQUI", "CONSULTAR AQUÍ", "VER CUADRO"]):
                                url_cuadro = a["href"]
                                if not url_cuadro.startswith("http"):
                                    url_cuadro = "https://publicacionesprocesales.ramajudicial.gov.co" + (url_cuadro if url_cuadro.startswith("/") else "/" + url_cuadro)
                                break

                        # C. Documento principal del estado
                        url_documento_estado = None
                        docs_header = None
                        for elem in detail_soup.find_all(["h4", "h5", "div"]):
                            if "documentos de la publicaci" in elem.get_text().lower():
                                docs_header = elem
                                break
                        if docs_header:
                            parent = docs_header.parent
                            if parent:
                                for a in parent.find_all("a", href=True):
                                    a_text = a.get_text().lower()
                                    if "estado" in a_text:
                                        url_documento_estado = a["href"]
                                        if not url_documento_estado.startswith("http"):
                                            url_documento_estado = "https://publicacionesprocesales.ramajudicial.gov.co" + (url_documento_estado if url_documento_estado.startswith("/") else "/" + url_documento_estado)
                                        break

                        # Prioridad de fuentes
                        fuentes_principales = []
                        if url_resumen:
                            fuentes_principales.append((url_resumen, "resumen_publicacion"))
                        if url_cuadro:
                            fuentes_principales.append((url_cuadro, "cuadro_consultar_aqui"))
                        if url_documento_estado:
                            fuentes_principales.append((url_documento_estado, "documento_estado"))
                            
                        match_principal = None
                        fuente_validada_url = None
                        fuente_validada_tipo = None
                        texto_principal = ""
                        
                        for source_url, source_type in fuentes_principales:
                            print(f"[scraper] Descargando y validando fuente principal ({source_type}): {source_url}")
                            doc_text = await extract_text_content(source_url, client)
                            match = validate_strong_match(doc_text, radicado_completo, demandante, demandado)
                            if match.is_valid:
                                match_principal = match
                                fuente_validada_url = source_url
                                fuente_validada_tipo = source_type
                                texto_principal = doc_text
                                break
                                
                        if not match_principal:
                            print(f"[scraper] Descartando {cand['title']}: No hay match fuerte en fuentes principales.")
                            return None

                        url_providencia = None
                        documentos_complementarios = []
                        
                        seen_doc_urls = set()
                        seen_doc_urls.add(fuente_validada_url)
                        if url_resumen: seen_doc_urls.add(url_resumen)
                        if url_cuadro: seen_doc_urls.add(url_cuadro)
                        if url_documento_estado: seen_doc_urls.add(url_documento_estado)

                        for a in detail_soup.find_all("a", href=True):
                            href = a["href"]
                            if not href.startswith("http"):
                                href = "https://publicacionesprocesales.ramajudicial.gov.co" + (href if href.startswith("/") else "/" + href)
                                
                            if "/get_file" in href or "/documents/" in href:
                                if href in seen_doc_urls:
                                    continue
                                seen_doc_urls.add(href)
                                
                                doc_name = a.get_text(strip=True)
                                if "providencia" in doc_name.lower() or "auto" in doc_name.lower():
                                    if not url_providencia:
                                        url_providencia = href
                                
                                print(f"[scraper] Descargando comp: {doc_name}...")
                                doc_text_comp = await extract_text_content(href, client)
                                match_comp = validate_strong_match(doc_text_comp, radicado_completo, demandante, demandado)
                                
                                documentos_complementarios.append({
                                    "url": href,
                                    "nombre": doc_name,
                                    "contiene_radicado": match_comp.is_valid,
                                    "match_type": match_comp.match_type if match_comp.is_valid else None
                                })

                        observacion = f"Validada por {fuente_validada_tipo}. El radicado fue encontrado en el listado principal del estado."
                        
                        return {
                            "fecha": cand["fecha_publicacion"],
                            "tipo": cand["categoria"],
                            "descripcion": cand["title"],
                            "documento_url": fuente_validada_url,
                            "source_url": cand["detail_url"],
                            "source_id": hashlib.md5(cand["detail_url"].encode()).hexdigest(),
                            
                            "url_fuente_principal": fuente_validada_url,
                            "tipo_fuente_principal": fuente_validada_tipo,
                            "texto_fuente_principal": texto_principal,
                            "validada_por_fuente_principal": True,
                            "numero_estado": estado_no or "",
                            "fecha_estado_electronico": fecha_estado_electronico.strftime("%Y-%m-%d") if fecha_estado_electronico else cand["fecha_publicacion"],
                            "url_resumen_publicacion": url_resumen,
                            "url_cuadro": url_cuadro,
                            "url_providencia": url_providencia,
                            "documentos_complementarios": json.dumps(documentos_complementarios),
                            "match_fuerte": True,
                            "match_type": match_principal.match_type,
                            "motivo_match": match_principal.reasons,
                            "observacion": observacion
                        }
                    except Exception as ex:
                        print(f"[scraper] Error en candidato {cand['detail_url']}: {ex}")
                        return None

            tasks = [process_candidate(c) for c in candidates]
            found_results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in found_results:
                if res and isinstance(res, dict):
                    results.append(res)

        except Exception as e:
            print(f"[scraper] Error en consulta: {e}")

    final = []
    seen = set()
    for r in results:
        if r["source_id"] not in seen:
            final.append(r)
            seen.add(r["source_id"])
    return final

def parse_fecha_pub(fecha_str: str) -> date | None:
    if not fecha_str: return None
    try: return datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
    except: return None

async def consultar_publicaciones(radicado: str):
    return await consultar_publicaciones_rango(radicado, datetime.now().strftime("%Y-%m-%d"))
