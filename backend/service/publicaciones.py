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
    
    t_norm = "".join(normalize_text(text).split())
    rad_norm = "".join(filter(str.isdigit, radicado_completo))
    
    # Al menos dos palabras significativas de cada parte (o todas si hay menos de 2)
    def significant_words(name):
        if not name: return []
        # Normalizar: quitar sufijos comunes y palabras vacías
        n = name.upper().replace("S.A.S.", "").replace("SAS", "").replace("S.A.", "").replace("LIMITADA", "").replace("LTDA", "").replace("E.S.P.", "").replace("ESP", "")
        # IMPORTANTE: Devolver en minúsculas para que coincida con t_norm
        return [w.lower() for w in n.split() if len(w) > 3 and w not in ["BANCO", "SISTEMA", "GESTION", "COBRANZAS", "MUNICIPIO", "PARA", "LAS", "LOS", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA"]]
        
    words_dante = significant_words(demandante)
    words_dado = significant_words(demandado)
    
    matches_dante = sum(1 for w in words_dante if w in t_norm) if words_dante else 0
    matches_dado = sum(1 for w in words_dado if w in t_norm) if words_dado else 0
    
    threshold_dante = min(2, len(words_dante)) if words_dante else 0
    threshold_dado = min(2, len(words_dado)) if words_dado else 0
    
    match_dante = (matches_dante >= threshold_dante) if threshold_dante > 0 else True
    match_dado = (matches_dado >= threshold_dado) if threshold_dado > 0 else True
    
    # 1. Match Exacto por número de 23 dígitos
    # Exigimos que coincidan las partes si están especificadas para evitar falsos positivos
    if rad_norm in t_norm:
        if (match_dante or match_dado) or (not words_dante and not words_dado):
            print(f"[validator] MATCH OK: Radicado 23 dígitos + Partes (Dante:{match_dante}, Dado:{match_dado})")
            return True
        else:
            print(f"[validator] RADICADO OK pero PARTES FAIL. Descartando.")
            return False
    
    # 2. Match por Patrón Año + Consecutivo (12:21)
    # Aquí exigimos patrón + que al menos una parte coincida + que el número de despacho esté en el texto
    pattern = rad_norm[12:21]
    court_num = radicado_completo[9:12] # e.g. '024'
    court_num_short = str(int(court_num)) # e.g. '24'
    
    if pattern in t_norm:
        # Verificar que mencione al despacho target (ya sea '024' o '24')
        if court_num in t_norm or f"juzgado{court_num_short}" in t_norm or f"j{court_num_short}" in t_norm or f"cmpl{court_num_short}bt" in t_norm:
            if match_dante or match_dado:
                print(f"[validator] MATCH OK: Patrón {pattern} + Despacho {court_num} + Al menos una parte.")
                return True
        
    print(f"[validator] MATCH FAIL: No coincide radicado completo ni (patrón + despacho + ambas partes).")
    return False

async def get_candidates(html: str, radicado_completo: str, fecha_act_min: Optional[date] = None):
    candidates = []
    soup = BeautifulSoup(html, "html.parser")
    
    # Liferay search results are usually in entries
    entries = soup.find_all("div", class_="search-result") or soup.find_all("li", class_="search-result")
    if not entries:
        entries = [l.parent.parent for l in soup.find_all("a", href=True) if "find_file_entry" in l["href"] or "/documents/" in l["href"]]

    year_pattern = radicado_completo[12:16]
    consecutive = radicado_completo[16:21]
    pattern_with_dash = f"{year_pattern}-{consecutive}"

    seen_urls = set()
    for entry in entries:
        l = entry.find("a", href=True)
        if not l: continue
        url = l["href"]
        if url in seen_urls: continue
        seen_urls.add(url)
        
        if not url.startswith("http"):
            url = "https://publicacionesprocesales.ramajudicial.gov.co" + (url if url.startswith("/") else "/" + url)
            
        entry_text = entry.get_text()
        
        # 1. Extraer Fecha (Validar que sea igual o posterior)
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', entry_text)
        pub_date = None
        if date_match:
            try:
                d, m, y = date_match.groups()
                pub_date = date(int(y), int(m), int(d))
            except: pass
        
        if fecha_act_min and pub_date and pub_date < fecha_act_min:
            continue

        # 2. Identificar si es un documento directo o una página de resumen (Como la Imagen 3 del Word)
        # Si es una página de resumen, necesitamos entrar para buscar el PDF real.
        is_direct_doc = any(ext in url.lower() for ext in [".pdf", ".docx", "find_file_entry"])
        
        # Pre-filtrado por año y despacho en el texto del entry / enlace
        # radicado_completo es de 23 dígitos: e.g. 11001400302420240140300
        # despacho es radicado_completo[9:12] -> '024'
        # año es radicado_completo[12:16] -> '2024'
        despacho_target = radicado_completo[9:12]
        year_target = radicado_completo[12:16]
        
        # Extraer posibles años de 4 dígitos en el texto del candidato
        years_in_text = re.findall(r'\b(20\d{2})\b', entry_text)
        if years_in_text and year_target not in years_in_text:
            print(f"[scraper] Descartando candidato por año incorrecto en texto (años: {years_in_text}, año buscado: {year_target})")
            continue
            
        # Extraer posibles códigos de despacho (3 dígitos) en el texto del candidato
        despachos_in_text = re.findall(r'\b(\d{3})\b', entry_text)
        if despachos_in_text and despacho_target not in despachos_in_text:
            print(f"[scraper] Descartando candidato por despacho incorrecto en texto (despachos: {despachos_in_text}, despacho buscado: {despacho_target})")
            continue
        
        # 3. Candidato si menciona el patrón
        if pattern_with_dash in entry_text or consecutive in entry_text:
            candidates.append({
                "fecha": pub_date.strftime("%Y-%m-%d") if pub_date else datetime.now().strftime("%Y-%m-%d"),
                "tipo": l.get_text(strip=True)[:100] or "Publicación Procesal",
                "documento_url": url,
                "source_id": hashlib.md5(url.encode()).hexdigest(),
                "snippet": entry_text[:200],
                "is_direct": is_direct_doc
            })
    return candidates

MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

async def consultar_publicaciones_rango(radicado_completo: str, fecha_act_str: str, demandante: str = "", demandado: str = ""):
    results = []
    rad_digits = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_digits) < 21: return []
    
    fecha_act_min = parse_fecha_pub(fecha_act_str)
    pattern_with_dash = f"{rad_digits[12:16]}-{rad_digits[16:21]}"
    despacho_12 = rad_digits[:12]
    
    # Preparar tags de año y mes para búsqueda dirigida (Paso a Paso del usuario)
    tags = []
    if fecha_act_min:
        tags.append(str(fecha_act_min.year))
        tags.append(MONTHS_ES[fecha_act_min.month - 1])

    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        # Semáforo para no saturar el portal
        sem = asyncio.Semaphore(2)

        # Query ultra-precisa: Despacho (12) + Radicado Corto (YYYY-NNNNN)
        # Esto reduce drásticamente los resultados basura y evita el cuelgue al 5%
        queries = [f"{despacho_12} {pattern_with_dash}"]
        
        # Fallback: Si la ultra-precisa no devuelve nada, probamos radicado solo
        queries.append(pattern_with_dash)
        
        for i, q in enumerate(queries):
            if results: break # Si ya encontramos, no seguimos buscando
            
            params = {"q": q}
            # En la segunda vuelta (menos precisa), aplicamos los tags de mes/año del Word
            if i > 0 and tags:
                params["tag"] = tags
            
            print(f"[scraper] Buscando profundidad con query: {q} params: {params}")
            try:
                resp = await client.get("https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search", params=params)
                if resp.status_code == 200:
                    all_candidates = await get_candidates(resp.text, rad_digits, fecha_act_min)
                    
                    # LIMITAMOS a los mejores 15 candidatos pre-filtrados para evitar cuelgues (5% hang)
                    candidates = all_candidates[:15]
                    
                    async def process_candidate(cand):
                        async with sem:
                            target_url = cand["documento_url"]
                            try:
                                if not cand["is_direct"]:
                                    print(f"[scraper] Navegando página de resumen: {target_url}")
                                    inner_resp = await client.get(target_url)
                                    if inner_resp.status_code == 200:
                                        inner_soup = BeautifulSoup(inner_resp.text, "html.parser")
                                        inner_links = inner_soup.find_all("a", href=True)
                                        for il in inner_links:
                                            link_text = il.get_text().upper()
                                            href = il["href"]
                                            # Solo si parece un PDF o documento
                                            if any(k in link_text for k in ["VER", "CONSULTAR", "AQUI", "DETALLE"]) or ".pdf" in href.lower():
                                                if not href.startswith("http"):
                                                    href = "https://publicacionesprocesales.ramajudicial.gov.co" + (href if href.startswith("/") else "/" + href)
                                                
                                                doc_text = await extract_text_content(href, client)
                                                if validate_content(doc_text, rad_digits, demandante, demandado):
                                                    new_cand = cand.copy()
                                                    new_cand["documento_url"] = href
                                                    return new_cand
                                else:
                                    # Si es directo, igual validamos contenido
                                    doc_text = await extract_text_content(target_url, client)
                                    if validate_content(doc_text, rad_digits, demandante, demandado):
                                        return cand
                            except Exception as e:
                                print(f"[scraper] Error procesando candidato {target_url}: {e}")
                        return None

                    tasks = [process_candidate(c) for c in candidates]
                    found_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for res in found_results:
                        if res and isinstance(res, dict): 
                            results.append(res)
                
            except Exception as e:
                print(f"[scraper] Error en query {q}: {e}")

    # Deduplicar resultados finales
    final = []
    seen = set()
    for r in results:
        if r["source_id"] not in seen:
            final.append(r); seen.add(r["source_id"])
    return final

def parse_fecha_pub(fecha_str: str) -> date | None:
    if not fecha_str: return None
    try: return datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
    except: return None

async def consultar_publicaciones(radicado: str):
    return await consultar_publicaciones_rango(radicado, datetime.now().strftime("%Y-%m-%d"))
