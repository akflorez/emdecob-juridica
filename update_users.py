from backend.db import SessionLocal
from backend.models import User, Case
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')
db = SessionLocal()

company_id = 1

users_to_create = [
    ('julian.cuartas', 'JULIAN CUARTAS', '292509', 'COORDINADOR'),
    ('valentina.patino', 'VALENTINA PATIÑO', '251410', 'COORDINADOR'),
    ('heriberto.montealegre', 'HERIBERTO MONTEALEGRE', 'Heriberto2026*', 'COMERCIAL'),
    ('santiago.quintero', 'SANTIAGO QUINTERO', '251016', 'ABOGADO'),
    ('erik.garzon', 'ERIK SANTIAGO GARZON AMEZQUITA', '1094950684', 'COORDINADOR'),
    ('erik.santiago', 'ERIK SANTIAGO GARZON AMEZQUITA', '1094950684', 'COORDINADOR')
]

# Buscar empresa de fna_juridica
fna = db.query(User).filter(User.username == "fna_juridica").first()
fna_company_id = fna.company_id if fna else 2

for uname, name, pwd, role in users_to_create:
    user = db.query(User).filter(User.username == uname).first()
    cid = fna_company_id if 'erik' in uname else company_id
    scope = 'ALL' if 'erik' in uname else 'COMPANY'
    if not user:
        user = User(
            username=uname,
            nombre=name,
            hashed_password=pwd_context.hash(pwd),
            role=role,
            cases_view_scope=scope,
            company_id=cid
        )
        db.add(user)
    else:
        user.nombre = name
        user.hashed_password = pwd_context.hash(pwd)
        user.role = role
        user.cases_view_scope = scope
        user.company_id = cid

db.commit()

santiago = db.query(User).filter(User.username == 'santiago.quintero').first()
emdecob_user = db.query(User).filter(User.username == 'juricob').first()
cases = db.query(Case).filter(Case.user_id == emdecob_user.id).all()
count = 0
for c in cases:
    if c.abogado != santiago.nombre:
        c.abogado = santiago.nombre
        count += 1

db.commit()
print(f'Actualizados {count} casos a abogado {santiago.nombre}. Usuarios creados con exito.')
