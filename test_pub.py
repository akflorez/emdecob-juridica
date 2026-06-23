import asyncio
from backend.db import SessionLocal
from backend.service.publicaciones import consultar_publicaciones_rango
from backend.models import CasePublicationSearch, Case

async def main():
    db = SessionLocal()
    # find case 11001400300520240143900
    case = db.query(Case).filter(Case.radicado == "11001400300520240143900").first()
    if not case:
        print("Case not found")
        return
        
    print(f"Case found: {case.radicado}, demandante: {case.demandante}, demandado: {case.demandado}")
    
    # Let's search month 01, year 2025? or month 02?
    # Let's check existing searches
    searches = db.query(CasePublicationSearch).filter(CasePublicationSearch.radicado == case.radicado).all()
    for s in searches:
        print(f"Search: {s.fecha_inicio_busqueda} - {s.estado_busqueda}")
        
    # Test query for a known month, say 2024-05? or whenever the case was published
    # Let's run a test query with 2024-05
    results = await consultar_publicaciones_rango(
        radicado_completo=case.radicado,
        fecha_act_str="2024-05-01",
        demandante=case.demandante or "",
        demandado=case.demandado or "",
        year=2024,
        month=10,
        company_id=case.company_id,
        search_id=9999
    )
    
    print("Results:")
    for r in results:
        print(f" - {r.get('fecha')} | {r.get('tipo')} | validacion: {r.get('estado_validacion')} | score: {r.get('match_score')}")

if __name__ == "__main__":
    asyncio.run(main())
