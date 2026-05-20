import httpx
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..models.publicacion_procesal import PublicacionProcesal
from ..db import SessionLocal

# Constants for the external portal
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co"
SEARCH_ENDPOINT = f"{BASE_URL}/web/publicaciones-procesales/inicio"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def _parse_radicado(radicado_completo: str) -> Dict[str, str]:
    """Extract components from the full radicado string.
    Expected format: 11001400302420240140300 (despacho+year+number)
    Returns a dict with keys: despacho, year, number, full.
    """
    # First 12 chars are despacho code, next 4 are year, remaining are number
    despacho = radicado_completo[:12]
    year = radicado_completo[12:16]
    number = radicado_completo[16:]
    return {
        "despacho": despacho,
        "year": year,
        "number": number,
        "full": radicado_completo,
    }

def _build_query_params(components: Dict[str, str]) -> Dict[str, str]:
    """Construct the GET parameters required by the portal.
    The portal expects filters like the year, the despacho code and the radicado number.
    """
    # The portal uses the following GET params (observed from manual browsing)
    # - "anno"   : year of the radicado
    # - "despacho": despacho code (12‑digit)
    # - "numero" : the numeric part of the radicado (after the year)
    # - "texto"  : optional free‑text search, we feed the full radicado for robustness
    return {
        "anno": components["year"],
        "despacho": components["despacho"],
        "numero": components["number"],
        "texto": components["full"],
    }

def _fetch_search_page(params: Dict[str, str]) -> Optional[str]:
    """Perform the HTTP GET to the portal and return raw HTML if successful.
    Returns ``None`` when the request fails or the portal returns a non‑200 status.
    """
    try:
        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            response = client.get(SEARCH_ENDPOINT, params=params)
            response.raise_for_status()
            return response.text
    except Exception as exc:
        # Log the error in real code – for now we just return None
        print(f"[publicaciones_service] Error fetching search page: {exc}")
        return None

def _extract_candidates(html: str) -> List[Dict[str, Any]]:
    """Parse the search results page and extract candidate publications.
    The portal lists each result in a table row with links to the document and detail page.
    We collect the URL, title, and any visible metadata.
    """
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []
    # The actual HTML structure may change; we try a few heuristics.
    # Look for rows inside a table with class "resultados" or generic "tbody".
    table = soup.find("table")
    if not table:
        return results
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if not cols:
            continue
        # Typically first column holds the document link
        link_tag = cols[0].find("a", href=True)
        if not link_tag:
            continue
        doc_url = link_tag["href"]
        # Ensure absolute URL
        if doc_url.startswith("/"):
            doc_url = BASE_URL + doc_url
        title = link_tag.get_text(strip=True)
        # Additional metadata may be in other columns – we capture raw text
        meta = " ".join(col.get_text(strip=True) for col in cols[1:])
        results.append({"url": doc_url, "title": title, "meta": meta})
    return results

def _validate_candidate(candidate: Dict[str, Any], radicado: str) -> bool:
    """Very light validation – the portal already filters by radicado.
    We additionally check that the radicado string appears in the title or metadata.
    """
    needle = radicado
    return needle in candidate["title"] or needle in candidate["meta"]

def _persist_publication(session: Session, radicado: str, data: Dict[str, Any]) -> PublicacionProcesal:
    """Insert or update a publication record.
    If a record with the same URL already exists, we update its metadata.
    """
    existing = (
        session.query(PublicacionProcesal)
        .filter(PublicacionProcesal.url_detalle == data["url"])
        .first()
    )
    if existing:
        existing.titulo = data.get("title")
        existing.meta = data.get("meta")
        existing.radicado = radicado
        existing.fuente = "Publicaciones Procesales Rama Judicial"
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        return existing
    else:
        new_pub = PublicacionProcesal(
            radicado=radicado,
            despacho_codigo=radicado[:12],
            url_detalle=data["url"],
            titulo=data.get("title"),
            meta=data.get("meta"),
            fuente="Publicaciones Procesales Rama Judicial",
            estado_busqueda="fetched",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(new_pub)
        return new_pub

def buscar_publicaciones(radicado_completo: str) -> List[PublicacionProcesal]:
    """Public entry point used by the API router.
    Returns a list of persisted ``PublicacionProcesal`` objects for the supplied radicado.
    """
    components = _parse_radicado(radicado_completo)
    params = _build_query_params(components)
    html = _fetch_search_page(params)
    if not html:
        return []
    candidates = _extract_candidates(html)
    valid = [c for c in candidates if _validate_candidate(c, radicado_completo)]
    if not valid:
        return []
    session = SessionLocal()
    persisted: List[PublicacionProcesal] = []
    try:
        for cand in valid:
            pub = _persist_publication(session, radicado_completo, cand)
            persisted.append(pub)
        session.commit()
    except Exception as exc:
        session.rollback()
        print(f"[publicaciones_service] DB error: {exc}")
    finally:
        session.close()
    return persisted
