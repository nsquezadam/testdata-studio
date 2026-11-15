from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db import get_db
from app.models.audit import Audit
from app.models.user import Role, User
from app.schemas.users import (
    RoleResponse,
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)


router = APIRouter(
    prefix="/users",
    tags=["Gestión de usuarios"],
)


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


def _cargar_usuario(db: Session, usuario_id: int) -> User | None:
    return db.scalar(
        select(User)
        .options(joinedload(User.rol))
        .where(User.usuario_id == usuario_id)
    )


def _respuesta_usuario(user: User) -> UserResponse:
    return UserResponse(
        usuario_id=user.usuario_id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        rol_id=user.rol_id,
        rol=user.rol.nombre,
        estado=user.estado,
        fecha_creacion=user.fecha_creacion,
    )


# ============================================================
# CONSULTAR ROLES DISPONIBLES
# ============================================================

@router.get(
    "/roles",
    response_model=list[RoleResponse],
)
def listar_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrador")),
):
    roles = db.scalars(
        select(Role)
        .where(Role.estado.is_(True))
        .order_by(Role.rol_id)
    ).all()

    return roles


# ============================================================
# LISTAR USUARIOS
# ============================================================

@router.get(
    "",
    response_model=list[UserResponse],
)
def listar_usuarios(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrador")),
):
    usuarios = db.scalars(
        select(User)
        .options(joinedload(User.rol))
        .order_by(User.usuario_id)
    ).unique().all()

    return [_respuesta_usuario(usuario) for usuario in usuarios]


# ============================================================
# CREAR USUARIO
# ============================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_usuario(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrador")),
):
    email = _normalizar_email(payload.email)

    usuario_existente = db.scalar(
        select(User).where(User.email == email)
    )

    if usuario_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario registrado con ese correo electrónico.",
        )

    rol = db.scalar(
        select(Role).where(Role.rol_id == payload.rol_id)
    )

    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil seleccionado no existe.",
        )

    if not rol.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil seleccionado no se encuentra habilitado.",
        )

    usuario = User(
        rol_id=payload.rol_id,
        nombre=payload.nombre.strip(),
        apellido=payload.apellido.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        estado=True,
    )

    db.add(usuario)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el usuario debido a datos duplicados.",
        ) from None

    usuario_creado = _cargar_usuario(db, usuario.usuario_id)

    if usuario_creado is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El usuario fue creado, pero no pudo ser recuperado.",
        )

    return _respuesta_usuario(usuario_creado)


# ============================================================
# MODIFICAR USUARIO
# ============================================================

@router.put(
    "/{usuario_id}",
    response_model=UserResponse,
)
def modificar_usuario(
    usuario_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    administrador: User = Depends(require_roles("Administrador")),
):
    usuario = _cargar_usuario(db, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    email = _normalizar_email(payload.email)

    email_existente = db.scalar(
        select(User).where(
            User.email == email,
            User.usuario_id != usuario_id,
        )
    )

    if email_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro usuario registrado con ese correo electrónico.",
        )

    rol = db.scalar(
        select(Role).where(Role.rol_id == payload.rol_id)
    )

    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil seleccionado no existe.",
        )

    if not rol.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil seleccionado no se encuentra habilitado.",
        )

    # Evita que el único Administrador cambie accidentalmente
    # su propio perfil y pierda acceso administrativo.
    if (
        usuario.usuario_id == administrador.usuario_id
        and payload.rol_id != usuario.rol_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede modificar su propio perfil de acceso.",
        )

    usuario.nombre = payload.nombre.strip()
    usuario.apellido = payload.apellido.strip()
    usuario.email = email
    usuario.rol_id = payload.rol_id

    if payload.password is not None:
        usuario.password_hash = hash_password(payload.password)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible modificar el usuario.",
        ) from None

    usuario_actualizado = _cargar_usuario(db, usuario_id)

    if usuario_actualizado is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El usuario fue modificado, pero no pudo ser recuperado.",
        )

    return _respuesta_usuario(usuario_actualizado)


# ============================================================
# ACTIVAR / DESACTIVAR USUARIO + RF16
# ============================================================

@router.patch(
    "/{usuario_id}/estado",
    response_model=UserResponse,
)
def cambiar_estado_usuario(
    usuario_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    administrador: User = Depends(require_roles("Administrador")),
):
    usuario = _cargar_usuario(db, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    if usuario.usuario_id == administrador.usuario_id and not payload.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivar su propia cuenta.",
        )

    if usuario.estado == payload.estado:
        estado_texto = "activo" if payload.estado else "inactivo"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario ya se encuentra {estado_texto}.",
        )

    estado_anterior = usuario.estado

    usuario.estado = payload.estado

    auditoria = Audit(
        usuario_id=administrador.usuario_id,
        entidad_afectada="USUARIO",
        registro_id=usuario.usuario_id,
        estado_anterior=estado_anterior,
        estado_nuevo=payload.estado,
    )

    db.add(auditoria)

    try:
        # IMPORTANTE:
        # UPDATE usuario + INSERT auditoria
        # se confirman juntos en una sola transacción.
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible actualizar el estado del usuario.",
        ) from None

    usuario_actualizado = _cargar_usuario(db, usuario_id)

    if usuario_actualizado is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El usuario fue actualizado, pero no pudo ser recuperado.",
        )

    return _respuesta_usuario(usuario_actualizado)