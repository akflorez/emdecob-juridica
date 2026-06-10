import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db import Base
from backend.models import Case, CasePublication
from backend.service.publicaciones import build_portal_search_url, guardar_publicacion_validada

@pytest.fixture(scope='function')
def db_session():
    # Use in‑memory SQLite for fast isolated tests
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()

def test_build_portal_search_url_contains_delta():
    url = build_portal_search_url('123456', '2024-01-01', '2024-01-31')
    assert '_${PORTLET_ID}_delta' in url or 'delta' in url
    # Ensure the delta parameter is present and set to 100 (as defined in code)
    assert 'delta=100' in url

def test_guardar_publicacion_validada_uniqueness(db_session):
    # Create a case
    case = Case(radicado='1234567890')
    db_session.add(case)
    db_session.commit()
    # First publication data
    data = {
        'radicado': case.radicado,
        'case_id': case.id,
        'fecha_publicacion': '2024-02-01',
        'url_fuente_principal': 'http://example.com/doc.pdf',
        'tipo_fuente_principal': 'pdf',
        'texto_fuente_principal': 'some text',
        'validada_por_fuente_principal': True,
        'match_fuerte': True,
    }
    # Save first time
    pub1 = guardar_publicacion_validada(db_session, data)
    db_session.commit()
    assert pub1 is not None
    # Attempt to save duplicate for same case
    pub2 = guardar_publicacion_validada(db_session, data)
    db_session.commit()
    # Should not create a new row, returns the existing one (or None) – we check count
    count = db_session.query(CasePublication).filter(CasePublication.case_id == case.id).count()
    assert count == 1

def test_is_relevant_actuacion_normalization():
    from backend.service.publicaciones import is_relevant_actuacion
    # Accents, spacing, case-insensitivity
    assert is_relevant_actuacion("AUTO  resuelve  algo") is True
    assert is_relevant_actuacion("Fijación  de estado") is True
    assert is_relevant_actuacion("Notificación por estado") is True
    assert is_relevant_actuacion("TRASLADO especial") is True
    assert is_relevant_actuacion("no relevante") is False

def test_auto_queue_publicaciones_for_case(db_session):
    from backend.models import Case, CaseEvent, CasePublicationSearch
    from backend.service.publicaciones import auto_queue_publicaciones_for_case
    from datetime import date
    
    # 1. Create case with company_id
    case = Case(radicado='11001400302420240140300', company_id=2)
    db_session.add(case)
    db_session.commit()
    
    # 2. Add relevant events
    # Event 1: April 10, day < 25 -> Should only enqueue April
    ev1 = CaseEvent(case_id=case.id, event_date=date(2026, 4, 10), title="AUTO REQUIERE", event_hash="hash1")
    # Event 2: May 27, day >= 25 -> Should enqueue May and June
    ev2 = CaseEvent(case_id=case.id, event_date=date(2026, 5, 27), title="FIJACION ESTADO", event_hash="hash2")
    db_session.add(ev1)
    db_session.add(ev2)
    db_session.commit()
    
    # Run auto queue
    queued = auto_queue_publicaciones_for_case(db_session, case)
    
    # Verify enqueued count
    # April 2026, May 2026, June 2026 -> 3 searches should be enqueued
    assert queued == 3
    
    # Verify db entries
    searches = db_session.query(CasePublicationSearch).filter(CasePublicationSearch.radicado == case.radicado).all()
    assert len(searches) == 3
    months = {s.mes_busqueda for s in searches}
    assert months == {"2026-04", "2026-05", "2026-06"}
    
    for s in searches:
        assert s.company_id == 2
        assert s.estado == "pendiente"
        
    # Re-run without force -> Should not duplicate
    queued_again = auto_queue_publicaciones_for_case(db_session, case)
    assert queued_again == 0
    assert db_session.query(CasePublicationSearch).filter(CasePublicationSearch.radicado == case.radicado).count() == 3
    
    # Re-run with force -> Should reactivate and not duplicate
    s_april = db_session.query(CasePublicationSearch).filter(
        CasePublicationSearch.radicado == case.radicado,
        CasePublicationSearch.mes_busqueda == "2026-04"
    ).first()
    s_april.estado = "error"
    s_april.intentos = 2
    s_april.ultimo_error = "some error"
    db_session.commit()
    
    queued_force = auto_queue_publicaciones_for_case(db_session, case, force=True)
    assert queued_force == 3 # All 3 are forced (reset)
    
    # Check April was reset
    db_session.refresh(s_april)
    assert s_april.estado == "pendiente"
    assert s_april.intentos == 0
    assert s_april.ultimo_error is None

