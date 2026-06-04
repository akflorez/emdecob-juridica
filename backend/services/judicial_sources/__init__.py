from .config import JUDICIAL_SOURCE_URLS, MULTISOURCE_ENABLED, MULTISOURCE_DRY_RUN
from .base import JudicialSourceConnector
from .publicaciones_source import PublicacionesProcesalesConnector
from .tyba_source import TybaConnector
from .siugj_source import SiugjConnector
from .samai_source import SamaiConnector

# Registry of available connectors
CONNECTORS = {
    "PUBLICACIONES_PROCESALES": PublicacionesProcesalesConnector(),
    "TYBA": TybaConnector(),
    "SIUGJ": SiugjConnector(),
    "SAMAI": SamaiConnector()
}
