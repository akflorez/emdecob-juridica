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

async def get_candidates(html: str, radicado_completo: str):
    candidates = []
    soup = BeautifulSoup(html, "html.parser")
    # Capturar TODOS los links que parezcan resultados
    # Liferay suele usar h6/h3 para títulos de búsqueda o divs.search-result
    links = soup.find_all("a", href=True)
    
    year_pattern = radicado_completo[12:16]
    consecutive = radicado_completo[16:21]

    seen_urls = set()
    for l in links:
        url = l["href"]
        if "find_file_entry" not in url and not url.lower().endswith(".pdf") and not url.lower().endswith(".docx"):
            continue
        if url in seen_urls: continue
        seen_urls.add(url)
        
        # Limpiar URL
        if not url.startswith("http"):
            url = "https://publicacionesprocesales.ramajudicial.gov.co" + (url if url.startswith("/") else "/" + url)
            
        # Extraer Metadata del contenedor del link
        parent = l.parent
        while parent and len(parent.get_text()) < 50:
            parent = parent.parent
        
        txt = parent.get_text() if parent else l.get_text()
        
        # Candidato si menciona el año o el patrón
        if year_pattern in txt or consecutive in txt:
            candidates.append({
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "tipo": l.get_text(strip=True)[:100],
                "documento_url": url,
                "source_id": hashlib.md5(url.encode()).hexdigest()
            })
    return candidates

async def consultar_publicaciones_rango(radicado_completo: str, fecha_act_str: str, demandante: str = "", demandado: str = ""):
    results = []
    rad_digits = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_digits) < 21: return []
    
    # Patrones de búsqueda
    pattern = f"{rad_digits[12:16]}-{rad_digits[16:21]}"
    search_queries = [rad_digits, pattern]
    if demandado and demandado.strip():
        parts = demandado.split()
        if parts:
            search_queries.append(parts[0])

    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        for q in search_queries:
            if not q: continue
            print(f"[scraper] Buscando query: {q}")
            try:
                resp = await client.get("https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search", params={"q": q})
                if resp.status_code == 200:
                    candidates = await get_candidates(resp.text, rad_digits)
                    print(f"[scraper] Encontrados {len(candidates)} candidatos para validacion.")
                    for cand in candidates[:8]: # Revisar máximo 8 para eficiencia
                        text = await extract_text_content(cand["documento_url"], client)
                        if validate_content(text, rad_digits, demandante, demandado):
                            results.append(cand)
                            print(f"[scraper] ✅ Documento verificado exitosamente.")
            except Exception as e:
                print(f"[scraper] Error en búsqueda '{q}': {e}")
            if results: break

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
