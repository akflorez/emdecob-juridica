import pytest
import unittest.mock as mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db import Base
from backend.models import Case, CaseEvent, CasePublication, CaseSearchSourceResult, User, Company
from backend.service.fallback_search import search_radicado_with_fallbacks, FALLBACK_TYBA_ENABLED
from backend.services.judicial_sources import CONNECTORS

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(scope='function')
def db_session():
    # In-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create default company and users
    comp = Company(id=1, nombre="Empresa Default")
    user = User(id=1, username="test_user", company_id=1, is_admin=False, is_superadmin=False, hashed_password="dummy")
    super_user = User(id=2, username="superadmin", company_id=None, is_admin=True, is_superadmin=True, hashed_password="dummy")
    
    session.add(comp)
    session.add(user)
    session.add(super_user)
    session.commit()
    
    yield session
    session.close()
    engine.dispose()

@pytest.mark.anyio
async def test_search_rama_principal_success(db_session):
    # Setup: mock validar_radicado_completo to simulate finding case in Rama Judicial
    async def mock_validar(radicado, db, is_new_import=False):
        c = Case(radicado=radicado, company_id=1, juzgado="Juzgado Civil Circuito")
        db.add(c)
        db.flush()
        return {"found": True, "case": c}
        
    user = db_session.query(User).filter(User.id == 1).first()
    
    with mock.patch("backend.main.validar_radicado_completo", new=mock_validar):
        res = await search_radicado_with_fallbacks(
            radicado="11001400302420240140300",
            company_id=1,
            db=db_session,
            current_user=user,
            force=True
        )
        
        assert res["status"] == "found"
        assert res["source"] == "rama_judicial"
        assert res["case"].radicado == "11001400302420240140300"
        
        # Verify check log
        log = db_session.query(CaseSearchSourceResult).filter(
            CaseSearchSourceResult.fuente == "RAMA_JUDICIAL"
        ).first()
        assert log is not None
        assert log.encontrado is True
        assert log.confianza == 100

@pytest.mark.anyio
async def test_search_fallback_alternative_success(db_session):
    # Setup: mock validar_radicado_completo to return not found
    async def mock_validar(radicado, db, is_new_import=False):
        return {"found": False, "case": None}
        
    user = db_session.query(User).filter(User.id == 1).first()
    
    with mock.patch("backend.main.validar_radicado_completo", new=mock_validar):
        # We search a valid 23-digit radicado
        rad = "11001418902720250002800"
        res = await search_radicado_with_fallbacks(
            radicado=rad,
            company_id=1,
            db=db_session,
            current_user=user,
            force=True
        )
        
        # Publicaciones Procesales connector supports len=23 and yields success stub details
        assert res["status"] == "found_alternative"
        assert res["source"] == "publicaciones_procesales"
        assert res["confidence"] == 90
        assert res["requiere_revision"] is False
        
        # Check case was created in DB
        case = db_session.query(Case).filter(Case.radicado == rad, Case.company_id == 1).first()
        assert case is not None
        assert case.juzgado == "Juzgado Administrativo de Despacho"
        assert case.fuente_encontrado == "PUBLICACIONES_PROCESALES"
        assert case.encontrado_en_fuente_alternativa is True
        
        # Check alternative log
        log_rama = db_session.query(CaseSearchSourceResult).filter(
            CaseSearchSourceResult.fuente == "RAMA_JUDICIAL"
        ).first()
        assert log_rama is not None
        assert log_rama.encontrado is False
        
        log_pub = db_session.query(CaseSearchSourceResult).filter(
            CaseSearchSourceResult.fuente == "PUBLICACIONES_PROCESALES"
        ).first()
        assert log_pub is not None
        assert log_pub.encontrado is True
        assert log_pub.confianza == 90
        assert log_pub.case_id == case.id
        
        # Check events were created
        events = db_session.query(CaseEvent).filter(CaseEvent.case_id == case.id).all()
        assert len(events) > 0
        assert events[0].title == "Auto de publicación de estado"
        assert events[0].company_id == 1
        
        # Check publications were created
        pubs = db_session.query(CasePublication).filter(CasePublication.case_id == case.id).all()
        assert len(pubs) > 0
        assert pubs[0].tipo_publicacion == "Auto"
        assert pubs[0].company_id == 1

@pytest.mark.anyio
async def test_search_not_found(db_session):
    async def mock_validar(radicado, db, is_new_import=False):
        return {"found": False, "case": None}
        
    user = db_session.query(User).filter(User.id == 1).first()
    
    # Mock publications connector search_case to return not found
    with mock.patch("backend.main.validar_radicado_completo", new=mock_validar):
        connector = CONNECTORS.get("PUBLICACIONES_PROCESALES")
        with mock.patch.object(connector, "search_case", return_value={"status": "not_found", "message": "No encontrado"}):
            rad = "11001418902720250002800"
            res = await search_radicado_with_fallbacks(
                radicado=rad,
                company_id=1,
                db=db_session,
                current_user=user,
                force=True
            )
            
            assert res["status"] == "not_found"
            assert "rama_judicial" in res["sources_checked"]
            assert "publicaciones_procesales" in res["sources_checked"]
            
            # Case should not be created
            case = db_session.query(Case).filter(Case.radicado == rad, Case.company_id == 1).first()
            assert case is None

@pytest.mark.anyio
async def test_no_overwrite_existing_good_data(db_session):
    # If case already exists with good data, alternative fallback should not overwrite it
    case = Case(
        radicado="11001418902720250002800",
        company_id=1,
        juzgado="Juzgado del Circuito Principal",
        demandante="Demandante Fuerte Original",
        demandado="Demandado Fuerte Original",
        encontrado_en_fuente_alternativa=False
    )
    db_session.add(case)
    db_session.commit()
    
    async def mock_validar(radicado, db, is_new_import=False):
        return {"found": False, "case": None}
        
    user = db_session.query(User).filter(User.id == 1).first()
    
    with mock.patch("backend.main.validar_radicado_completo", new=mock_validar):
        res = await search_radicado_with_fallbacks(
            radicado=case.radicado,
            company_id=1,
            db=db_session,
            current_user=user,
            force=True
        )
        
        # Verify fallback found it, but case fields were NOT overwritten
        assert res["status"] == "found_alternative"
        db_session.refresh(case)
        assert case.juzgado == "Juzgado del Circuito Principal" # Unaltered
        assert case.demandante == "Demandante Fuerte Original" # Unaltered
        assert case.demandado == "Demandado Fuerte Original" # Unaltered
        # Empty/missing fields like departamento/municipio should be filled
        assert case.departamento == "No especificado"

@pytest.mark.anyio
async def test_superadmin_company_required(db_session):
    superadmin = db_session.query(User).filter(User.username == "superadmin").first()
    
    # Query without specifying company_id -> should return error
    res = await search_radicado_with_fallbacks(
        radicado="11001418902720250002800",
        company_id=None,
        db=db_session,
        current_user=superadmin,
        force=True
    )
    
    assert res["status"] == "error"
    assert "empresa" in res["message"].lower()

@pytest.mark.anyio
async def test_case_matching_confidence_tiers(db_session):
    async def mock_validar(radicado, db, is_new_import=False):
        return {"found": False, "case": None}
        
    user = db_session.query(User).filter(User.id == 1).first()
    
    # 1. Moderado (70 to 84 confidence)
    connector = CONNECTORS.get("PUBLICACIONES_PROCESALES")
    mock_moderado = {
        "status": "success",
        "url": "http://alternative.source/123",
        "data": {
            "radicado": "11001418902720250002800",
            "despacho": "Juzgado Administrativo",
            "confianza_busqueda": 75,
            "encontrado_en_fuente_alternativa": True,
            "requiere_revision": True
        }
    }
    
    with mock.patch("backend.main.validar_radicado_completo", new=mock_validar):
        with mock.patch.object(connector, "search_case", return_value=mock_moderado):
            rad = "11001418902720250002800"
            res = await search_radicado_with_fallbacks(
                radicado=rad,
                company_id=1,
                db=db_session,
                current_user=user,
                force=True
            )
            
            assert res["status"] == "found_alternative"
            assert res["confidence"] == 75
            assert res["requiere_revision"] is True
            
            case = db_session.query(Case).filter(Case.radicado == rad, Case.company_id == 1).first()
            assert case is not None
            assert case.requiere_revision is True
            
    # Clean up created case
    db_session.delete(case)
    db_session.commit()
            
    # 2. Débil (< 70 confidence) -> should not confirm case
    mock_debil = {
        "status": "success",
        "url": "http://alternative.source/123",
        "data": {
            "radicado": "11001418902720250002800",
            "despacho": "Juzgado Administrativo",
            "confianza_busqueda": 60,
            "encontrado_en_fuente_alternativa": True,
            "requiere_revision": True
        }
    }
    
    with mock.patch("backend.main.validar_radicado_completo", new=mock_validar):
        with mock.patch.object(connector, "search_case", return_value=mock_debil):
            res_debil = await search_radicado_with_fallbacks(
                radicado=rad,
                company_id=1,
                db=db_session,
                current_user=user,
                force=True
            )
            
            assert res_debil["status"] == "not_found"
            
            # Verify no case was created
            case_debil = db_session.query(Case).filter(Case.radicado == rad, Case.company_id == 1).first()
            assert case_debil is None
