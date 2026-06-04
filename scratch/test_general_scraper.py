import asyncio
from backend.service.publicaciones import consultar_publicaciones_rango

async def test_case(radicado, demandante, demandado, date_str):
    print(f"\n==================================================")
    print(f"TESTING RADICADO: {radicado}")
    print(f"Demandante: {demandante} | Demandado: {demandado}")
    print(f"==================================================")
    res = await consultar_publicaciones_rango(radicado, date_str, demandante, demandado)
    print(f"Results found: {len(res)}")
    for r in res:
        print(f"- Date: {r['fecha']}")
        print(f"  Type: {r['tipo']}")
        print(f"  URL: {r['documento_url']}")

async def main():
    # Test a few sample cases
    await test_case(
        "63401408900220240026600",
        "FONDO NACIONAL DEL AHORRO S.A.",
        "DUVAN SANTOS SAAVEDRA",
        "2024-01-01"
    )
    await test_case(
        "68077408900120240032800",
        "FONDO NACIONAL DEL AHORRO S.A.",
        "BLANCA RUTH RONCANCIO DE FORERO",
        "2024-01-01"
    )

if __name__ == "__main__":
    asyncio.run(main())
