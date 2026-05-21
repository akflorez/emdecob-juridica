from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..service.publicaciones_service import buscar_publicaciones
from ..models.publicacion_procesal import PublicacionProcesal
from ..db import SessionLocal
from ..auth import get_current_user  # assuming existing auth dependency

router = APIRouter(prefix="/api/v1/publicaciones", tags=["Publicaciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{radicado}", response_model=List[PublicacionProcesal])
async def get_publicaciones(radicado: str, db: SessionLocal = Depends(get_db), user: dict = Depends(get_current_user)):
    """Return the list of publications for the given radicado.
    The service will fetch from the external portal if no records exist yet.
    """
    # First try to load existing records
    existing = db.query(PublicacionProcesal).filter(PublicacionProcesal.radicado == radicado).all()
    if existing:
        return existing
    # If none, trigger a fresh search
    results = buscar_publicaciones(radicado)
    if not results:
        raise HTTPException(status_code=404, detail="No publications found for this radicado")
    return results
