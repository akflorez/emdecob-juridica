import os
import httpx
import asyncio
import random

BASE_URL = os.getenv("RAMA_BASE_URL", "https://consultaprocesos.ramajudicial.gov.co:448/api/v2")

# Headers completos de navegador real (Chrome en Windows)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://consultaprocesos.ramajudicial.gov.co",
    "Referer": "https://consultaprocesos.ramajudicial.gov.co/",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Configuración de reintentos
MAX_RETRIES = 3
BASE_DELAY = 1.0  # segundos
MAX_DELAY = 10.0  # segundos


class RamaError(Exception):
    pass


class RamaRateLimitError(RamaError):
    """Error específico para rate limiting (403/429)"""
    pass


async def _get(path: str, params: dict | None = None, retry_count: int = 0):
    """
    Hace GET a la API de Rama Judicial con reintentos y backoff exponencial.
    """
    url = f"{BASE_URL}{path}"

    # Delay aleatorio pequeño entre peticiones para evitar parecer bot
    if retry_count == 0:
        await asyncio.sleep(random.uniform(0.1, 0.3))

    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=30,
            follow_redirects=True,
            http2=True
        ) as client:
            r = await client.get(url, params=params)

        # Rate limiting o bloqueo
        if r.status_code in (403, 429):
            if retry_count < MAX_RETRIES:
                delay = min(BASE_DELAY * (2 ** retry_count) + random.uniform(0.5, 1.5), MAX_DELAY)
                print(f"⚠️ Rate limit ({r.status_code}), reintentando en {delay:.1f}s... (intento {retry_count + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                return await _get(path, params, retry_count + 1)
            else:
                raise RamaRateLimitError(f"Rama Judicial bloqueó la petición después de {MAX_RETRIES} intentos. Espera unos minutos.")

        # Otros errores de servidor (500, 502, 503, 504)
        if r.status_code >= 500:
            if retry_count < MAX_RETRIES:
                delay = min(BASE_DELAY * (2 ** retry_count) + random.uniform(0.5, 1.5), MAX_DELAY)
                print(f"⚠️ Error servidor ({r.status_code}), reintentando en {delay:.1f}s...")
                await asyncio.sleep(delay)
                return await _get(path, params, retry_count + 1)
            else:
                raise RamaError(f"Rama Judicial {r.status_code}: Error del servidor")

        # Error 404 - no encontrado (no reintentar)
        if r.status_code == 404:
            return None

        # Otros errores
        if r.status_code != 200:
            raise RamaError(f"Rama Judicial {r.status_code}: {r.text[:300]}")

        try:
            return r.json()
        except Exception:
            raise RamaError("Rama Judicial respondió pero no es JSON válido.")

    except httpx.TimeoutException:
        if retry_count < MAX_RETRIES:
            delay = min(BASE_DELAY * (2 ** retry_count), MAX_DELAY)
            print(f"⚠️ Timeout, reintentando en {delay:.1f}s...")
            await asyncio.sleep(delay)
            return await _get(path, params, retry_count + 1)
        raise RamaError("Timeout: Rama Judicial no respondió a tiempo")

    except httpx.ConnectError as e:
        if retry_count < MAX_RETRIES:
            delay = min(BASE_DELAY * (2 ** retry_count), MAX_DELAY)
            print(f"⚠️ Error de conexión, reintentando en {delay:.1f}s...")
            await asyncio.sleep(delay)
            return await _get(path, params, retry_count + 1)
        raise RamaError(f"Error de conexión con Rama Judicial: {str(e)}")


async def consulta_por_radicado(radicado: str, solo_activos: bool = False, pagina: int = 1):
    """Consulta un proceso por número de radicado."""
    params = {
        "numero": radicado,
        "SoloActivos": "true" if solo_activos else "false",
        "pagina": pagina,
    }

    try:
        result = await _get("/Proceso/NumeroRadicacion", params=params)
        if result is not None:
            return result
    except RamaError:
        pass

    return await _get("/Procesos/Consulta/NumeroRadicacion", params=params)


async def consultar_por_radicado(radicado: str, solo_activos: bool = False, pagina: int = 1):
    """Alias para compatibilidad."""
    return await consulta_por_radicado(radicado, solo_activos=solo_activos, pagina=pagina)


async def detalle_proceso(id_proceso: int):
    """Obtiene el detalle de un proceso por su ID."""
    try:
        result = await _get(f"/Proceso/Detalle/{int(id_proceso)}")
        if result is not None:
            return result
    except RamaError:
        pass

    return await _get(f"/Procesos/Detalle/{int(id_proceso)}")


async def actuaciones_proceso(id_proceso: int, pagina: int = 1):
    """Obtiene las actuaciones de un proceso por su ID."""
    data = await _get(f"/Proceso/Actuaciones/{int(id_proceso)}", params={"pagina": pagina})

    if data is None:
        return []
    if isinstance(data, dict):
        return data.get("actuaciones") or data.get("items") or []
    if isinstance(data, list):
        return data
    return []


async def delay_between_requests(seconds: float = 0.5):
    """Delay entre peticiones para evitar rate limiting."""
    await asyncio.sleep(seconds + random.uniform(0, 0.3))


def _normalize_documentos(raw) -> list:
    """
    Normaliza la respuesta de cualquier endpoint de documentos a una lista plana.

    La Rama Judicial puede responder en varios formatos:
      - Lista directa:           [ {idRegistroDocumento: X, ...}, ... ]
      - Dict con clave conocida: { "documentos": [...] }  |  { "items": [...] }
      - Dict único doc:          { "idRegistroDocumento": X, ... }
      - None / vacío:            None  |  []  |  {}
    """
    if not raw:
        return []

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        # Intentar claves habituales de la API
        for key in (
            "documentos", "Documentos",
            "items", "Items",
            "data", "Data",
            "result", "Result",
            "documentosActuacion", "DocumentosActuacion",
        ):
            val = raw.get(key)
            if val and isinstance(val, list):
                return val

        # Si el dict mismo parece ser un documento (tiene campo de ID)
        id_keys = ("idRegistroDocumento", "IdRegistroDocumento", "idDocumento", "IdDocumento", "id")
        if any(k in raw for k in id_keys):
            return [raw]

    return []


# =======================================================
# DOCUMENTOS DE ACTUACIÓN — con múltiples rutas de fallback
# =======================================================
async def documentos_actuacion(id_reg_actuacion: int, llave_proceso: str = "") -> list:
    """
    Obtiene los documentos PDF de una actuación específica.
    URL confirmada: GET /api/v2/Proceso/DocumentosActuacion/{id_reg_actuacion}
    El parámetro llave_proceso ya NO es necesario en este endpoint.
    """
    iid = int(id_reg_actuacion)

    # ── Ruta confirmada por inspección de red en la página oficial ──
    # URL real: GET /api/v2/Proceso/DocumentosActuacion/{id_reg_actuacion}
    # Sin parámetro llaveProceso — la Rama no lo requiere en este endpoint
    primary_path = f"/Proceso/DocumentosActuacion/{iid}"

    # Rutas alternativas de fallback (por si cambia en el futuro)
    candidate_paths = [
        primary_path,
        f"/Proceso/Actuacion/Documentos/{iid}",
        f"/Proceso/Actuacion/{iid}/Documentos",
        f"/Proceso/Documento/{iid}",
    ]

    last_error: Exception | None = None

    for path in candidate_paths:
        try:
            # La ruta primaria no necesita params; las de fallback pueden intentarlo también sin params
            print(f"📄 [rama.py] Probando: GET {BASE_URL}{path}")
            raw = await _get(path, params=None)
            print(f"📄 [rama.py] Respuesta raw (tipo={type(raw).__name__}): {str(raw)[:400]}")

            docs = _normalize_documentos(raw)

            if docs:
                print(f"📄 [rama.py] ✅ {len(docs)} documentos encontrados con: {path}")
                return docs

            print(f"📄 [rama.py] {path} respondió vacío — probando siguiente...")

        except RamaError as e:
            print(f"📄 [rama.py] ⚠️ Error en {path}: {e}")
            last_error = e
            if isinstance(e, RamaRateLimitError):
                raise

    print(f"📄 [rama.py] ❌ Ninguna ruta devolvió documentos para idRegActuacion={iid}")
    if last_error:
        raise last_error

    return []