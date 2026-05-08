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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
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

async def extract_text_content(url: str, client: httpx.AsyncClient) -> str:
    try:
        print(f"[validator] Descargando {url[:100]}...")
        resp = await client.get(url, timeout=35)
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
    
    # 1. Match Exacto por número de 23 dígitos
    if rad_norm in t_norm:
        print(f"[validator] MATCH OK: Radicado de 23 dígitos encontrado.")
        return True
        
    # 2. Match por Patrón Año + Consecutivo (12:21)
    pattern = rad_norm[12:21]
    if pattern in t_norm:
        dante_norm = normalize_text(demandante)
        dado_norm = normalize_text(demandado)
        
        # Al menos un apellido significativo de cada parte
        def significant_words(name):
            return [w for w in name.split() if len(w) > 4 and w not in ["banco", "sistema", "gestion", "cobranzas", "municipio"]]
            
        words_dante = significant_words(dante_norm)
        words_dado = significant_words(dado_norm)
        
        match_dante = any(w in t_norm for w in words_dante) if words_dante else True
        match_dado = any(w in t_norm for w in words_dado) if words_dado else True
        
        if match_dante and match_dado:
            print(f"[validator] MATCH OK: Patrón {pattern} + Nombres validados.")
            return True
            
    print(f"[validator] MATCH FAIL: No coincide radicado ni partes.")
    return False

async def get_candidates(html: str, radicado_completo: str, fecha_act_min: Optional[date] = None):
    candidates = []
    soup = BeautifulSoup(html, "html.parser")
    
    # Liferay search results are usually in entries
    entries = soup.find_all("div", class_="search-result") or soup.find_all("li", class_="search-result")
    if not entries:
        # Fallback a buscar por contenedores genéricos de links
        entries = [l.parent.parent for l in soup.find_all("a", href=True) if "find_file_entry" in l["href"]]

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
        
        # 1. Extraer Fecha del Texto del Resultado
        # Buscamos patrones tipo DD/MM/YYYY o YYYY-MM-DD
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', entry_text)
        pub_date = None
        if date_match:
            try:
                d, m, y = date_match.groups()
                pub_date = date(int(y), int(m), int(d))
            except: pass
        
        # 2. Validar Fecha (Igual o posterior a la actuación)
        if fecha_act_min and pub_date:
            if pub_date < fecha_act_min:
                print(f"[scraper] Saltando publicacion antigua: {pub_date} < {fecha_act_min}")
                continue

        # 3. Candidato si menciona el patrón o el radicado
        if pattern_with_dash in entry_text or consecutive in entry_text:
            candidates.append({
                "fecha": pub_date.strftime("%Y-%m-%d") if pub_date else datetime.now().strftime("%Y-%m-%d"),
                "tipo": l.get_text(strip=True)[:100] or "Notificación de Estado",
                "documento_url": url,
                "source_id": hashlib.md5(url.encode()).hexdigest(),
                "snippet": entry_text[:200]
            })
    return candidates

async def consultar_publicaciones_rango(radicado_completo: str, fecha_act_str: str, demandante: str = "", demandado: str = ""):
    results = []
    rad_digits = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_digits) < 21: return []
    
    # Fecha mínima de actuación para filtrar
    fecha_act_min = parse_fecha_pub(fecha_act_str)
    
    # Patrones de búsqueda según manual
    pattern_with_dash = f"{rad_digits[12:16]}-{rad_digits[16:21]}"
    despacho_12 = rad_digits[:12]
    
    # Priorizar búsqueda por despacho + patrón
    search_queries = [f"{despacho_12} {pattern_with_dash}", pattern_with_dash, rad_digits]
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        for q in search_queries:
            if not q: continue
            print(f"[scraper] Consultando portal con query: {q}")
            try:
                # El portal usa 'q' para búsqueda general
                resp = await client.get("https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search", params={"q": q})
                if resp.status_code == 200:
                    candidates = await get_candidates(resp.text, rad_digits, fecha_act_min)
                    print(f"[scraper] Encontrados {len(candidates)} candidatos potenciales.")
                    
                    for cand in candidates:
                        # Si el snippet ya tiene el patrón o nombres, validamos más rápido
                        if pattern_with_dash in cand["snippet"]:
                            results.append(cand)
                            print(f"[scraper] ✅ Match rápido por patrón en snippet.")
                            continue
                            
                        # Si no, descarga y valida contenido (último recurso)
                        text = await extract_text_content(cand["documento_url"], client)
                        if validate_content(text, rad_digits, demandante, demandado):
                            results.append(cand)
                            print(f"[scraper] ✅ Documento verificado por contenido.")
            except Exception as e:
                print(f"[scraper] Error en búsqueda '{q}': {e}")
            
            if results: break # Si encontramos resultados con la query más específica, paramos

    # Deduplicar
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
