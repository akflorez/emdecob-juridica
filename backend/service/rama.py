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
MAX_RETRIES = 5
BASE_DELAY = 1.5  # segundos
MAX_DELAY = 15.0  # segundos

# Semáforo global para limitar peticiones concurrentes a la Rama Judicial
# Aumentamos a 10 para mayor fluidez, ahora que liberamos el semáforo durante el sleep.
global_semaphore = asyncio.Semaphore(10)

# Caché simple en memoria para evitar repetir peticiones idénticas en corto tiempo
# Estructura: {(path, params_tuple): (timestamp, data)}
_rama_cache = {}
CACHE_TTL = 300  # 5 minutos (300 segundos)


class RamaError(Exception):
    pass


class RamaRateLimitError(RamaError):
    """Error específico para rate limiting (403/429)"""
    pass


async def _get(path: str, params: dict | None = None):
    """
    Hace GET a la API de Rama Judicial con reintentos, backoff exponencial,
    semaforización y caché.
    """
    import time

    # Generar llave de caché
    cache_key = (path, tuple(sorted(params.items())) if params else None)

    # 1. Verificar caché
    if cache_key in _rama_cache:
        timestamp, cached_data = _rama_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return cached_data

    # 2. Reintentos (Iterativo para liberar el semáforo durante el sleep)
    for retry_count in range(MAX_RETRIES + 1):
        # Usar semáforo para limitar concurrencia (SOLO durante la petición)
        async with global_semaphore:
            url = f"{BASE_URL}{path}"

            # Delay aleatorio pequeño entre peticiones para evitar parecer bot
            if retry_count == 0:
                await asyncio.sleep(random.uniform(0.1, 0.4))

            try:
                async with httpx.AsyncClient(
                    headers=HEADERS,
                    timeout=15,
                    follow_redirects=True,
                    http2=False
                ) as client:
                    r = await client.get(url, params=params)

                # Éxito
                if r.status_code == 200:
                    try:
                        data = r.json()
                        if data:
                            _rama_cache[cache_key] = (time.time(), data)
                        return data
                    except Exception:
                        raise RamaError("Respuesta de Rama Judicial no es JSON válido.")

                # Rate limiting o bloqueo
                if r.status_code in (403, 429):
                    if retry_count == MAX_RETRIES:
                        raise RamaRateLimitError(f"Bloqueo persistente (403/429) tras {MAX_RETRIES} intentos.")
                    print(f"⚠️ Rate limit ({r.status_code}), reintentando... ({retry_count + 1}/{MAX_RETRIES})")
                
                # Otros errores de servidor
                elif r.status_code >= 500:
                    if retry_count == MAX_RETRIES:
                        raise RamaError(f"Error persistente de servidor Rama ({r.status_code})")
                    print(f"⚠️ Error servidor ({r.status_code}), reintentando...")
                
                # 404 - no encontrado
                elif r.status_code == 404:
                    return None
                
                else:
                    raise RamaError(f"Error inesperado Rama ({r.status_code}): {r.text[:200]}")

            except (httpx.RequestError, asyncio.TimeoutError) as e:
                if retry_count == MAX_RETRIES:
                    raise RamaError(f"Falla crítica de conexión/timeout: {e}")
                print(f"⚠️ Error de red/timeout, reintentando...")

        # FUERA del 'async with global_semaphore': dormimos para el backoff
        delay = min(BASE_DELAY * (2 ** retry_count) + random.uniform(0.5, 2.0), MAX_DELAY)
        await asyncio.sleep(delay)

    return None


async def consulta_por_radicado(radicado: str, solo_activos: bool = False, pagina: int = 1):
    """Consulta un proceso por número de radicado."""
    params = {
        "numero": radicado,
        "SoloActivos": "true" if solo_activos else "false",
        "pagina": pagina,
    }

    # Intentar búsqueda estándar
    try:
        result = await _get("/Proceso/NumeroRadicacion", params=params)
        if result is not None:
            return result
    except RamaError:
        pass

    try:
        result = await _get("/Procesos/Consulta/NumeroRadicacion", params=params)
        if result is not None:
            return result
    except RamaError:
        pass

    # Fallback: Extraer departamento (primeros 2 dígitos) e intentar búsqueda con filtro
    if len(radicado) >= 2:
        id_depto = radicado[:2]
        params["idDepartamento"] = id_depto
        print(f"🌍 [rama.py] Intentando fallback con departamento {id_depto} para {radicado}")
        try:
            return await _get("/Proceso/NumeroRadicacion", params=params)
        except RamaError:
            pass

    return None


async def consultar_por_radicado(radicado: str, solo_activos: bool = False, pagina: int = 1):
    """Alias para compatibilidad."""
    return await consulta_por_radicado(radicado, solo_activos=solo_activos, pagina=pagina)


async def consulta_por_nombre(nombre: str, tipo_persona: int = 1, id_depto: str | None = None, solo_activos: bool = False, pagina: int = 1):
    """
    Consulta procesos por nombre o razón social.
    tipo_persona: 1 (Natural), 2 (Jurídica)
    """
    params = {
        "nombre": nombre,
        "tipoPersona": tipo_persona,
        "soloActivos": "true" if solo_activos else "false",
        "pagina": pagina,
    }
    if id_depto and id_depto != "00":
        params["idDepartamento"] = id_depto

    # Probamos las rutas habituales de la API v2
    paths = [
        "/Proceso/Consulta/NombreRazonSocial",
        "/Procesos/Consulta/NombreRazonSocial",
    ]
    
    for path in paths:
        try:
            result = await _get(path, params=params)
            if result:
                return result
        except RamaError:
            continue
            
    return None


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
    """Obtiene las actuaciones de un proceso por su ID con fallback."""
    paths = [
        f"/Proceso/Actuaciones/{int(id_proceso)}",
        f"/Procesos/Actuaciones/{int(id_proceso)}",
    ]
    
    for path in paths:
        try:
            print(f"[rama.py] Consultando actuaciones: {path}")
            data = await _get(path, params={"pagina": pagina})
            if data:
                res = []
                if isinstance(data, dict):
                    res = data.get("actuaciones") or data.get("items") or []
                elif isinstance(data, list):
                    res = data
                
                if res:
                    print(f"[rama.py] OK: {len(res)} actuaciones encontradas en {path}")
                    return res
        except RamaError as e:
            print(f"[rama.py] WARN: Error en {path}: {e}")
            continue

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