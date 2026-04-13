import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import engine, Base
from backend.main import _ensure_default_user

try:
    print("📋 Probando Base.metadata.create_all...")
    Base.metadata.create_all(bind=engine)
    print("✅ create_all exitoso")
    
    print("👤 Probando _ensure_default_user...")
    _ensure_default_user()
    print("✅ _ensure_default_user exitoso")
    
except Exception as e:
    print("❌ Error en startup:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
