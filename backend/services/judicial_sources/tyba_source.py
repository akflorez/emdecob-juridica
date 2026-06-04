from .base import JudicialSourceConnector
from .config import JUDICIAL_SOURCE_URLS

class TybaConnector(JudicialSourceConnector):
    source_name = "TYBA"
    
    def __init__(self):
        self.config = JUDICIAL_SOURCE_URLS.get(self.source_name, {})
        self.base_url = self.config.get("base_url", "https://procesojudicial.ramajudicial.gov.co/Justicia21/")
        self.consulta_url = self.config.get("consulta_url", "")
        
    def supports(self, radicado: str, metadata: dict = None) -> bool:
        return len(radicado) == 23 and radicado.isdigit()
        
    def search_case(self, radicado: str, metadata: dict = None) -> dict:
        if not self.supports(radicado, metadata):
            return {"status": "unsupported", "message": "Formato de radicado no soportado por esta fuente."}
            
        # Simulate captcha or manual interaction constraint
        # In Fase 1, since TYBA uses ASP.NET webforms and captchas/session tokens:
        return {
            "status": "unsupported",
            "source": self.source_name,
            "url": self.consulta_url or self.base_url,
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
            "url": self.consulta_url or self.base_url,
            "message": "Portal requiere validación manual o captcha."
        }
