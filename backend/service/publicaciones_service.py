import httpx
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..models.publicacion_procesal import PublicacionProcesal
from ..db import SessionLocal
from ..models.case import Case  # assuming a Case model exists with radicado and ultima_actuacion

# Constants for the external portal
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co"
SEARCH_ENDPOINT = f"{BASE_URL}/web/publicaciones-procesales/inicio"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_radicado(radicado_completo: str) -> Dict[str, str]:
    """Extract components from the full radicado string.
    Expected format: 11001400302420240140300 (despacho+year+number)
    Returns a dict with keys: despacho, year, number, full.
    """
    despacho = radicado_completo[:12]
    year = radicado_completo[12:16]
    number = radicado_completo[16:]
    return {"despacho": despacho, "year": year, "number": number, "full": radicado_completo}

def _get_case_actuation_date(radicado: str) -> Optional[date]:
    """Return the latest actuation date (ultima_actuacion) for the case.
    If not found, returns None.
    """
    session = SessionLocal()
    try:
        case_obj = session.query(Case).filter(Case.radicado == radicado).first()
        if case_obj and getattr(case_obj, "ultima_actuacion", None):
            return case_obj.ultima_actuacion
    finally:
        session.close()
    return None

def _first_day_of_month(dt: date) -> date:
    return dt.replace(day=1)

def _last_day_of_month(dt: date) -> date:
    next_month = dt.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

def _build_search_params(components: Dict[str, str], start: date, end: date) -> Dict[str, str]:
    """Construct GET parameters for a filtered portal search.
    The portal expects several hidden fields; we provide the visible ones.
    """
    return {
        "_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_action": "busqueda",
        "_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_fechaInicio": start.isoformat(),
        "_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_fechaFin": end.isoformat(),
        "_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_idDepto": "",
        "_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_idDespacho": components["despacho"],
        "_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_verTotales": "true",
    }

def _fetch_page(url: str, params: Optional[Dict[str, str]] = None) -> Optional[str]:
    try:
        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.text
    except Exception as exc:
        print(f"[publicaciones_service] Error fetching {url}: {exc}")
        return None

def _extract_cards(html: str) -> List[Dict[str, Any]]:
    """Parse search results and return a list of card dicts.
    Each card contains a detail URL and raw text for further validation.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards: List[Dict[str, Any]] = []
    for div in soup.find_all("div", class_=re.compile(r"card|portlet", re.I)):
        link = div.find("a", string=re.compile(r"Ver detalle", re.I))
        if not link or not link.get("href"):
            continue
        detail_url = link["href"]
        if detail_url.startswith("/"):
            detail_url = BASE_URL + detail_url
        text = div.get_text(separator=" ", strip=True)
        cards.append({"detail_url": detail_url, "raw_text": text})
    return cards

def _card_matches_despacho(card: Dict[str, Any], despacho: str) -> bool:
    return despacho in card["raw_text"]

def _fetch_detail_page(url: str) -> Optional[BeautifulSoup]:
    html = _fetch_page(url)
    if html:
        return BeautifulSoup(html, "html.parser")
    return None

def _parse_rows_from_detail(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract rows from the publication detail table.
    Expected columns: Número de estado, Fecha, Cuadro, Providencias.
    Returns list of dicts with keys: numero, fecha (date), cuadro_url, providencia_url.
    """
    rows: List[Dict[str, Any]] = []
    table = soup.find("table")
    if not table:
        return rows
    for tr in table.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) < 4:
            continue
        numero = cols[0].get_text(strip=True)
        fecha_str = cols[1].get_text(strip=True)
        try:
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        except Exception:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except Exception:
                continue
        cuadro_link = cols[2].find("a", href=True)
        providencia_link = cols[3].find("a", href=True)
        cuadro_url = cuadro_link["href"] if cuadro_link else None
        providencia_url = providencia_link["href"] if providencia_link else None
        if cuadro_url and cuadro_url.startswith("/"):
            cuadro_url = BASE_URL + cuadro_url
        if providencia_url and providencia_url.startswith("/"):
            providencia_url = BASE_URL + providencia_url
        rows.append({
            "numero": numero,
            "fecha": fecha,
            "cuadro_url": cuadro_url,
            "providencia_url": providencia_url,
        })
    return rows

def _download_pdf(url: str) -> Optional[bytes]:
    try:
        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as exc:
        print(f"[publicaciones_service] PDF download error {url}: {exc}")
        return None

def _pdf_text(content: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
        import io
        reader = PdfReader(io.BytesIO(content))
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        print(f"[publicaciones_service] PDF parsing error: {exc}")
        return ""

def _strong_match(radicado: str, despacho: str, text: str) -> bool:
    patterns = []
    # A: Full radicado
    patterns.append(re.escape(radicado))
    # B: Hyphenated full radicado (e.g., 11001-40-03-024-2024-01403-00)
    hyphenated = re.sub(r"(\d{5})(\d{2})(\d{2})(\d{3})(\d{4})(\d{5})", r"\1-\2-\3-\4-\5-\6", radicado)
    patterns.append(hyphenated)
    # C: Despacho + internal number
    patterns.append(despacho + radicado[12:])
    # D: Despacho with hyphens + internal number with hyphens
    desp_hy = re.sub(r"(\d{5})(\d{2})(\d{2})(\d{3})", r"\1-\2-\3-\4", despacho)
    internal_hy = radicado[12:16] + "-" + radicado[16:]
    patterns.append(desp_hy + " " + internal_hy)
    # E: Year-number block (radicado[12:])
    patterns.append(radicado[12:])
    for pat in patterns:
        if re.search(pat, text):
            return True
    return False

def _persist_publication(session: Session, radicado: str, despacho: str, data: Dict[str, Any]) -> PublicacionProcesal:
    existing = session.query(PublicacionProcesal).filter(PublicacionProcesal.url_detalle == data["detail_url"]).first()
    if existing:
        existing.titulo = data.get("title")
        existing.meta = data.get("meta")
        existing.fecha_publicacion = data.get("fecha_publicacion")
        existing.url_cuadro = data.get("cuadro_url")
        existing.url_providencia = data.get("providencia_url")
        existing.texto_cuadro = data.get("texto_cuadro")
        existing.texto_providencia = data.get("texto_providencia")
        existing.match_fuerte = data.get("match_fuerte")
        existing.match_type = data.get("match_type")
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        return existing
    else:
        new_pub = PublicacionProcesal(
            radicado=radicado,
            despacho_codigo=despacho,
            url_detalle=data.get("detail_url"),
            titulo=data.get("title"),
            meta=data.get("meta"),
            fecha_publicacion=data.get("fecha_publicacion"),
            url_cuadro=data.get("cuadro_url"),
            url_providencia=data.get("providencia_url"),
            texto_cuadro=data.get("texto_cuadro"),
            texto_providencia=data.get("texto_providencia"),
            match_fuerte=data.get("match_fuerte"),
            match_type=data.get("match_type"),
            fuente="Publicaciones Procesales Rama Judicial",
            estado_busqueda="fetched",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(new_pub)
        return new_pub

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def buscar_publicaciones(radicado_completo: str) -> List[PublicacionProcesal]:
    """Search, validate, and persist only confirmed publications for a radicado.
    Returns a list of persisted ``PublicacionProcesal`` objects; empty list means
    no valid publication was found.
    """
    components = _parse_radicado(radicado_completo)
    despacho = components["despacho"]
    act_date = _get_case_actuation_date(radicado_completo)
    if not act_date:
        print(f"[publicaciones_service] No actuation date for radicado {radicado_completo}")
        return []
    start_month = _first_day_of_month(act_date)
    end_month = _last_day_of_month(act_date)

    params = _build_search_params(components, start_month, end_month)
    search_html = _fetch_page(SEARCH_ENDPOINT, params=params)
    if not search_html:
        return []

    cards = _extract_cards(search_html)
    cards = [c for c in cards if _card_matches_despacho(c, despacho)]
    if not cards:
        return []

    session = SessionLocal()
    persisted: List[PublicacionProcesal] = []
    try:
        for card in cards:
            detail_soup = _fetch_detail_page(card["detail_url"])
            if not detail_soup:
                continue
            rows = _parse_rows_from_detail(detail_soup)
            rows = [r for r in rows if r["fecha"] >= act_date]
            for row in rows:
                cuadro_txt = ""
                if row["cuadro_url"]:
                    pdf_bytes = _download_pdf(row["cuadro_url"])
                    if pdf_bytes:
                        cuadro_txt = _pdf_text(pdf_bytes)
                is_strong = _strong_match(radicado_completo, despacho, cuadro_txt)
                if not is_strong:
                    print(f"[publicaciones_service] Discarded candidate from {row['cuadro_url']} – weak match")
                    continue
                providencia_txt = ""
                if row["providencia_url"]:
                    pdf_bytes = _download_pdf(row["providencia_url"])
                    if pdf_bytes:
                        providencia_txt = _pdf_text(pdf_bytes)
                data = {
                    "detail_url": card["detail_url"],
                    "title": card.get("title", ""),
                    "meta": card.get("meta", ""),
                    "fecha_publicacion": row["fecha"],
                    "cuadro_url": row["cuadro_url"],
                    "providencia_url": row["providencia_url"],
                    "texto_cuadro": cuadro_txt,
                    "texto_providencia": providencia_txt,
                    "match_fuerte": True,
                    "match_type": "strong",
                }
                pub_obj = _persist_publication(session, radicado_completo, despacho, data)
                persisted.append(pub_obj)
        session.commit()
    except Exception as exc:
        session.rollback()
        print(f"[publicaciones_service] DB error: {exc}")
    finally:
        session.close()
    return persisted
