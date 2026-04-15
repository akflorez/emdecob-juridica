import asyncio
from backend.service.publicaciones import consultar_publicaciones_rango

async def main():
    # Radicado del screenshot del usuario
    radicado = "13001400300220250090400"
    fecha = "2025-09-08" # Fecha del documento en la imagen
    demandante = "BANCO DAVIVIENDA S.A."
    demandado = "JUAN CARLOS QUINONEZ SALAMANCA" # Sin Ñ para mayor compatibilidad
    
    print(f"--- [TEST VISION INTERNA] ---")
    print(f"Buscando caso del screenshot: {radicado}")
    
    # Probamos con un rango que incluya la fecha del documento
    results = await consultar_publicaciones_rango(radicado, fecha, demandante, demandado)
    
    print(f"\n--- [RESULTADOS VALIDADOS] ---")
    print(f"Encontrados: {len(results)}")
    for r in results:
        print(f"FECHA: {r['fecha']} | TIPO: {r['tipo']}")
        print(f"URL: {r['documento_url']}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
