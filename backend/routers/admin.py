from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])
# All admin routes are implemented centrally in backend/main.py to prevent circular imports and path prefix collisions.
