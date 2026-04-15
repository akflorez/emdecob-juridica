import asyncio
from backend.service.publicaciones import consultar_publicaciones_rango, normalize_text, validate_content

async def main():
    radicado = "25286310500220240014000"
    fecha = "2024-06-01"
    demandante = "SISTEMA DE GESTION Y COBRANZAS S.A.S"
    demandado = "ALVARO IVAN GUERRERO PEREZ"
    
    print(f"--- [TEST] PROBANDO VISION INTERNA DE DOCUMENTOS ---")
    print(f"Radicado: {radicado}")
    print(f"Partes: {demandante} vs {demandado}")
    
    results = await consultar_publicaciones_rango(radicado, fecha, demandante, demandado)
    
    print(f"\n--- [RESULTADOS] ---")
    print(f"Publicaciones validadas encontradas: {len(results)}")
    for r in results:
        print(f"OK - FECHA: {r['fecha']} | TIPO: {r['tipo']}")
        print(f"   URL: {r['documento_url']}")
        print("-" * 20)
        
    if not results:
        print("FAIL - No se encontraron resultados validados.")

if __name__ == "__main__":
    asyncio.run(main())
