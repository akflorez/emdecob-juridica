import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from backend.main import list_cases, SessionLocal
from backend.models import User

db = SessionLocal()
u = db.query(User).filter(User.id == 2).first()
if u:
    try:
        # FastAPI endpoints depend on Query parameters being injected. 
        # For a manual call, we must pass the actual values, not let them default to Query().
        cases = list_cases(
            db=db, 
            current_user=u,
            search=None,
            juzgado=None,
            mes_actuacion=None,
            cedula=None,
            abogado=None,
            solo_validos=True,
            solo_pendientes=False,
            solo_no_leidos=False,
            solo_actualizados_hoy=False,
            con_documentos=None,
            page=1,
            page_size=20
        )
        print("Cases loaded successfully, count:", len(cases))
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("User 2 not found")
