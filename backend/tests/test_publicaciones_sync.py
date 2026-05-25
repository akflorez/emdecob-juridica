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
