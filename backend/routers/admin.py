from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.db import get_db
from backend.models import User, Company

# Lazy loader for superadmin dependency to prevent circular imports
def get_superadmin(current_user = Depends(lambda: __import__('backend.main', fromlist=['require_superadmin']).require_superadmin)):
    return current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Schemas
class CompanyCreate(BaseModel):
    nombre: str
    nit: Optional[str] = None
    limite_usuarios: int = 5

class CompanyOut(BaseModel):
    id: int
    nombre: str
    nit: Optional[str]
    estado: str
    limite_usuarios: int

    class Config:
        orm_mode = True

class UserCreateAdmin(BaseModel):
    username: str
    password: str
    nombre: str
    company_id: int
    email: Optional[str] = None
    is_admin: bool = False

class UserOutAdmin(BaseModel):
    id: int
    username: str
    nombre: Optional[str]
    company_id: Optional[int]
    is_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


@router.get("/companies", response_model=List[CompanyOut])
def list_companies(db: Session = Depends(get_db), _: User = Depends(get_superadmin)):
    return db.query(Company).order_by(Company.id).all()


@router.post("/companies", response_model=CompanyOut)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), _: User = Depends(get_superadmin)):
    new_company = Company(
        nombre=data.nombre,
        nit=data.nit,
        limite_usuarios=data.limite_usuarios
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


@router.get("/users", response_model=List[UserOutAdmin])
def list_users_admin(company_id: Optional[int] = None, db: Session = Depends(get_db), _: User = Depends(get_superadmin)):
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    return query.order_by(User.id).all()


@router.post("/users", response_model=UserOutAdmin)
def create_user_admin(data: UserCreateAdmin, db: Session = Depends(get_db), _: User = Depends(get_superadmin)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(400, "El username ya existe")
        
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(400, "La compañía no existe")

    from backend.main import _hash_password
    new_user = User(
        username=data.username,
        hashed_password=_hash_password(data.password),
        nombre=data.nombre,
        company_id=data.company_id,
        email=data.email,
        is_admin=data.is_admin,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
