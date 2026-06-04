import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db import Base
from backend.models import Case, CaseSourceCheck
from backend.services.judicial_sources import CONNECTORS
from backend.services.judicial_sources.source_router import run_multisource_check

@pytest.fixture(scope='function')
def db_session():
    # In-memory SQLite for testing DB operations
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()

def test_connectors_registered():
    assert "PUBLICACIONES_PROCESALES" in CONNECTORS
    assert "TYBA" in CONNECTORS
    assert "SIUGJ" in CONNECTORS
    assert "SAMAI" in CONNECTORS

def test_stubs_behavior():
    tyba = CONNECTORS["TYBA"]
    siugj = CONNECTORS["SIUGJ"]
    samai = CONNECTORS["SAMAI"]
    pub = CONNECTORS["PUBLICACIONES_PROCESALES"]
    
    radicado = "11001400300720180080000"
    
    # Test support checking
    assert tyba.supports(radicado)
    assert siugj.supports(radicado)
    assert samai.supports(radicado)
    assert pub.supports(radicado)
    
    # Test search_case returns unsupported/manual validation for the stubs
    res_tyba = tyba.search_case(radicado)
    assert res_tyba["status"] == "unsupported"
    assert "manual" in res_tyba["message"] or "captcha" in res_tyba["message"]
    
    res_siugj = siugj.search_case(radicado)
    assert res_siugj["status"] == "unsupported"
    assert "manual" in res_siugj["message"] or "captcha" in res_siugj["message"]
    
    res_samai = samai.search_case(radicado)
    assert res_samai["status"] == "unsupported"
    assert "manual" in res_samai["message"] or "captcha" in res_samai["message"]
    
    # Test Publicaciones search_case returns success
    res_pub = pub.search_case(radicado)
    assert res_pub["status"] == "success"

@pytest.mark.anyio
async def test_run_multisource_check_persists_logs(db_session):
    # Setup mock Case
    case = Case(
        id=999,
        radicado="11001400300720180080000",
        company_id=1,
        juzgado="Test Court"
    )
    db_session.add(case)
    db_session.commit()
    
    # Test run_multisource_check
    sources = ["PUBLICACIONES_PROCESALES", "TYBA", "SIUGJ", "SAMAI"]
    results = await run_multisource_check(
        radicado=case.radicado,
        company_id=case.company_id,
        case_id=case.id,
        sources=sources,
        dry_run=True, # Even with dry_run = True, the check logs should be written in Fase 1
        db=db_session
    )
    
    assert len(results) == 4
    
    # Verify database logs were created
    logs = db_session.query(CaseSourceCheck).filter(CaseSourceCheck.case_id == case.id).all()
    assert len(logs) == 4
    
    sources_logged = [l.source for l in logs]
    assert "PUBLICACIONES_PROCESALES" in sources_logged
    assert "TYBA" in sources_logged
    
    # Check that PUBLICACIONES_PROCESALES logged status "success"
    pub_log = next(l for l in logs if l.source == "PUBLICACIONES_PROCESALES")
    assert pub_log.status == "success"
    assert pub_log.records_found == 1
    assert pub_log.source_url == "https://publicacionesprocesales.ramajudicial.gov.co/"
    
    # Check that TYBA logged status "unsupported"
    tyba_log = next(l for l in logs if l.source == "TYBA")
    assert tyba_log.status == "unsupported"
    assert tyba_log.records_found == 0
