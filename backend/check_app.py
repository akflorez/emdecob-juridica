import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("🧪 Intentando importar FastAPI app...")
    from backend.main import app
    print("✅ Importación exitosa")
except Exception as e:
    print("❌ Error de importación:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
