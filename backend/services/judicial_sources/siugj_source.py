from .base import JudicialSourceConnector
from .config import JUDICIAL_SOURCE_URLS

class SiugjConnector(JudicialSourceConnector):
    source_name = "SIUGJ"
    
    def __init__(self):
        self.config = JUDICIAL_SOURCE_URLS.get(self.source_name, {})
        self.base_url = self.config.get("base_url", "https://siugj.ramajudicial.gov.co/principalPortal/index.php")
        self.consultas_externas_url = self.config.get("consultas_externas_url", "")
        
    def supports(self, radicado: str, metadata: dict = None) -> bool:
        return len(radicado) == 23 and radicado.isdigit()
        
    def search_case(self, radicado: str, metadata: dict = None) -> dict:
        if not self.supports(radicado, metadata):
            return {"status": "unsupported", "message": "Formato de radicado no soportado por esta fuente."}
            
        # SIUGJ requires user captcha/session token validation
        return {
            "status": "unsupported",
            "source": self.source_name,
            "url": self.consultas_externas_url or self.base_url,
            "message": "Fuente requiere validación manual, captcha o autenticación."
        }
        
    def search_events(self, radicado: str, metadata: dict = None) -> list:
        return []
        
    def search_documents(self, radicado: str, metadata: dict = None) -> list:
        return []
        
    def healthcheck(self) -> dict:
        return {
            "source": self.source_name,
            "status": "unsupported",
            "url": self.consultas_externas_url or self.base_url,
            "message": "Portal requiere validación manual o captcha."
        }
