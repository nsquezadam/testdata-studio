from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["Autenticación"])


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        usuario_id=user.usuario_id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        rol=user.rol.nombre,
        estado=user.estado,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(
        select(User)
        .options(joinedload(User.rol))
        .where(User.email == payload.email)
    )

    # CA04: no revelar cuál credencial específica es incorrecta.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña no válidos.",
        )

    # CA06: cuenta deshabilitada no puede iniciar sesión.
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta no se encuentra habilitada.",
        )

    if not user.rol.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El perfil asignado no se encuentra habilitado.",
        )

    token = create_access_token(user_id=user.usuario_id, role=user.rol.nombre)
    return LoginResponse(access_token=token, user=to_user_response(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)
