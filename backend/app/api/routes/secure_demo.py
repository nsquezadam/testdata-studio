from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.models.user import User


router = APIRouter(prefix="/secure", tags=["Permisos"])


@router.get("/admin")
def admin_only(
    current_user: User = Depends(require_roles("Administrador")),
):
    return {"message": "Acceso Administrador autorizado", "usuario_id": current_user.usuario_id}


@router.get("/analista")
def analyst_only(
    current_user: User = Depends(require_roles("Analista/Tester")),
):
    return {"message": "Acceso Analista/Tester autorizado", "usuario_id": current_user.usuario_id}
