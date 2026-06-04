class JudicialSourceConnector:
    source_name: str
    
    def supports(self, radicado: str, metadata: dict = None) -> bool:
        """Returns True if the radicado is supported by this source (e.g. correct length/format)."""
        raise NotImplementedError("Each connector must implement supports()")
        
    def search_case(self, radicado: str, metadata: dict = None) -> dict:
        """Performs a search on the official site for basic case details."""
        raise NotImplementedError("Each connector must implement search_case()")
        
    def search_events(self, radicado: str, metadata: dict = None) -> list:
        """Retrieves history of events/actuaciones."""
        raise NotImplementedError("Each connector must implement search_events()")
        
    def search_documents(self, radicado: str, metadata: dict = None) -> list:
        """Retrieves documents/annexes related to the case."""
        raise NotImplementedError("Each connector must implement search_documents()")
        
    def healthcheck(self) -> dict:
        """Checks if the official site is accessible/alive."""
        raise NotImplementedError("Each connector must implement healthcheck()")
