import sys
import os
sys.path.append(os.getcwd())
from backend.database import SessionLocal, Case
import json
from backend.service.publicaciones import is_relevant_actuacion

db = SessionLocal()
c = db.query(Case).filter(Case.radicado == '11001418902720250002800').first()
if c:
    acts = json.loads(c.actuaciones_json or '[]')
    print("Actuaciones:")
    for a in acts[:5]:
        print("-", a.get('anotacion'))
    print("Relevantes:", [a for a in acts if is_relevant_actuacion(a.get('anotacion'))])
else:
    print("Caso no encontrado")
