from .base import JudicialSourceConnector
from .config import JUDICIAL_SOURCE_URLS

class SamaiConnector(JudicialSourceConnector):
    source_name = "SAMAI"
    
    def __init__(self):
        self.config = JUDICIAL_SOURCE_URLS.get(self.source_name, {})
        self.base_url = self.config.get("base_url", "https://samai.consejodeestado.gov.co/")
        
    def supports(self, radicado: str, metadata: dict = None) -> bool:
        # SAMAI is for Consejo de Estado/Contentious administrative processes (23 digits)
        # We can check format, and also optionally check if the process category is administrative
        return len(radicado) == 23 and radicado.isdigit()
        
    def search_case(self, radicado: str, metadata: dict = None) -> dict:
        if not self.supports(radicado, metadata):
            return {"status": "unsupported", "message": "Formato de radicado no soportado por esta fuente."}
            
        # SAMAI requires captcha or session cookie validations
        return {
            "status": "unsupported",
            "source": self.source_name,
            "url": self.base_url,
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
            "url": self.base_url,
            "message": "Portal requiere validación manual o captcha."
        }
