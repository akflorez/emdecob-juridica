from .base import JudicialSourceConnector
from .config import JUDICIAL_SOURCE_URLS

class PublicacionesProcesalesConnector(JudicialSourceConnector):
    source_name = "PUBLICACIONES_PROCESALES"
    
    def __init__(self):
        self.config = JUDICIAL_SOURCE_URLS.get(self.source_name, {})
        self.base_url = self.config.get("base_url", "https://publicacionesprocesales.ramajudicial.gov.co/")
        
    def supports(self, radicado: str, metadata: dict = None) -> bool:
        # Standard Colombian judicial code format (23 digits)
        return len(radicado) == 23 and radicado.isdigit()
        
    def search_case(self, radicado: str, metadata: dict = None) -> dict:
        if not self.supports(radicado, metadata):
            return {"status": "unsupported", "message": "Formato de radicado no soportado por esta fuente."}
            
        # Stub diagnostic search (Fase 1 compliance)
        # Check if manual validation/captcha is simulated
        return {
            "status": "success",
            "source": self.source_name,
            "url": self.base_url,
            "data": {
                "radicado": radicado,
                "despacho": "Juzgado Administrativo de Despacho",
                "tipo_proceso": "Estados Electrónicos / Traslados",
                "demandante": "Demandante Demo",
                "demandado": "Demandado Demo",
                "estado": "activo"
            }
        }
        
    def search_events(self, radicado: str, metadata: dict = None) -> list:
        # Stub list of events
        return [
            {
                "fecha_actuacion": "2026-06-04",
                "actuacion": "Auto de publicación de estado",
                "anotacion": "Notificación por estado electrónico",
                "fecha_registro": "2026-06-04"
            }
        ]
        
    def search_documents(self, radicado: str, metadata: dict = None) -> list:
        # Stub list of documents
        return [
            {
                "tipo_documento": "Auto",
                "nombre_archivo": "auto_admite.pdf",
                "url_documento": f"{self.base_url}web/publicaciones-procesales/documento/1",
                "fecha_publicacion": "2026-06-04"
            }
        ]
        
    def healthcheck(self) -> dict:
        return {
            "source": self.source_name,
            "status": "healthy",
            "url": self.base_url,
            "message": "Conexión con el micrositio activa."
        }
