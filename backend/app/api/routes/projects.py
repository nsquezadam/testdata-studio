from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db import get_db
from app.models.audit import Audit
from app.models.project import DataModel, Project
from app.models.user import User
from app.schemas.projects import (
    DataModelCreate,
    DataModelResponse,
    DataModelStatusUpdate,
    DataModelUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectStatusUpdate,
    ProjectUpdate,
)


router = APIRouter(
    prefix="/projects",
    tags=["Proyectos y modelos"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _limpiar_texto(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value if value else None


def _cargar_proyecto(
    db: Session,
    proyecto_id: int,
) -> Project | None:
    return db.scalar(
        select(Project).where(
            Project.proyecto_id == proyecto_id
        )
    )


def _cargar_modelo(
    db: Session,
    modelo_id: int,
) -> DataModel | None:
    return db.scalar(
        select(DataModel).where(
            DataModel.modelo_id == modelo_id
        )
    )


def _cantidad_modelos(
    db: Session,
    proyecto_id: int,
) -> int:
    return db.scalar(
        select(func.count(DataModel.modelo_id))
        .where(
            DataModel.proyecto_id == proyecto_id
        )
    ) or 0


def _respuesta_proyecto(
    db: Session,
    proyecto: Project,
) -> ProjectResponse:
    return ProjectResponse(
        proyecto_id=proyecto.proyecto_id,
        usuario_id=proyecto.usuario_id,
        nombre=proyecto.nombre,
        descripcion=proyecto.descripcion,
        estado=proyecto.estado,
        fecha_creacion=proyecto.fecha_creacion,
        cantidad_modelos=_cantidad_modelos(
            db,
            proyecto.proyecto_id,
        ),
    )


# ============================================================
# CP-04-C01
# LISTAR PROYECTOS
# ============================================================

@router.get(
    "",
    response_model=list[ProjectResponse],
)
def listar_proyectos(
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    proyectos = db.scalars(
        select(Project)
        .order_by(Project.proyecto_id)
    ).all()

    return [
        _respuesta_proyecto(db, proyecto)
        for proyecto in proyectos
    ]


# ============================================================
# CP-04-C02
# CREAR PROYECTO
# ============================================================

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_proyecto(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    analista: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    nombre = payload.nombre.strip()

    proyecto_existente = db.scalar(
        select(Project).where(
            func.lower(Project.nombre)
            == nombre.lower()
        )
    )

    if proyecto_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un proyecto registrado "
                "con ese nombre."
            ),
        )

    proyecto = Project(
        usuario_id=analista.usuario_id,
        nombre=nombre,
        descripcion=_limpiar_texto(
            payload.descripcion
        ),
        estado=True,
    )

    db.add(proyecto)

    try:
        db.commit()
        db.refresh(proyecto)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el proyecto.",
        ) from None

    return _respuesta_proyecto(
        db,
        proyecto,
    )


# ============================================================
# CP-04-C03
# MODIFICAR PROYECTO
# ============================================================

@router.put(
    "/{proyecto_id}",
    response_model=ProjectResponse,
)
def modificar_proyecto(
    proyecto_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    proyecto = _cargar_proyecto(
        db,
        proyecto_id,
    )

    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )

    nombre = payload.nombre.strip()

    proyecto_existente = db.scalar(
        select(Project).where(
            func.lower(Project.nombre)
            == nombre.lower(),
            Project.proyecto_id != proyecto_id,
        )
    )

    if proyecto_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe otro proyecto "
                "registrado con ese nombre."
            ),
        )

    proyecto.nombre = nombre

    proyecto.descripcion = _limpiar_texto(
        payload.descripcion
    )

    try:
        db.commit()
        db.refresh(proyecto)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No fue posible modificar "
                "el proyecto."
            ),
        ) from None

    return _respuesta_proyecto(
        db,
        proyecto,
    )


# ============================================================
# CP-04-C04
# CREAR MODELO ASOCIADO
# ============================================================

@router.post(
    "/{proyecto_id}/models",
    response_model=DataModelResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_modelo(
    proyecto_id: int,
    payload: DataModelCreate,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    proyecto = _cargar_proyecto(
        db,
        proyecto_id,
    )

    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )

    if not proyecto.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se pueden agregar modelos "
                "a un proyecto inactivo."
            ),
        )

    nombre = payload.nombre.strip()

    modelo_existente = db.scalar(
        select(DataModel).where(
            DataModel.proyecto_id == proyecto_id,
            func.lower(DataModel.nombre)
            == nombre.lower(),
        )
    )

    if modelo_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un modelo con ese nombre "
                "dentro del proyecto."
            ),
        )

    modelo = DataModel(
        proyecto_id=proyecto_id,
        nombre=nombre,
        descripcion=_limpiar_texto(
            payload.descripcion
        ),
        estado=True,
    )

    db.add(modelo)

    try:
        db.commit()
        db.refresh(modelo)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el modelo.",
        ) from None

    return modelo


# ============================================================
# CP-04-C05
# LISTAR MODELOS DEL PROYECTO
# ============================================================

@router.get(
    "/{proyecto_id}/models",
    response_model=list[DataModelResponse],
)
def listar_modelos_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    proyecto = _cargar_proyecto(
        db,
        proyecto_id,
    )

    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )

    modelos = db.scalars(
        select(DataModel)
        .where(
            DataModel.proyecto_id == proyecto_id
        )
        .order_by(DataModel.modelo_id)
    ).all()

    return modelos


# ============================================================
# MODIFICAR MODELO
# ============================================================

@router.put(
    "/models/{modelo_id}",
    response_model=DataModelResponse,
)
def modificar_modelo(
    modelo_id: int,
    payload: DataModelUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    modelo = _cargar_modelo(
        db,
        modelo_id,
    )

    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo no encontrado.",
        )

    nombre = payload.nombre.strip()

    modelo_existente = db.scalar(
        select(DataModel).where(
            DataModel.proyecto_id
            == modelo.proyecto_id,
            func.lower(DataModel.nombre)
            == nombre.lower(),
            DataModel.modelo_id != modelo_id,
        )
    )

    if modelo_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe otro modelo con ese "
                "nombre dentro del proyecto."
            ),
        )

    modelo.nombre = nombre

    modelo.descripcion = _limpiar_texto(
        payload.descripcion
    )

    try:
        db.commit()
        db.refresh(modelo)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible modificar el modelo.",
        ) from None

    return modelo


# ============================================================
# CP-04-C07 / C08 / C09
# ACTIVAR / DESACTIVAR PROYECTO + RF16
# ============================================================

@router.patch(
    "/{proyecto_id}/estado",
    response_model=ProjectResponse,
)
def cambiar_estado_proyecto(
    proyecto_id: int,
    payload: ProjectStatusUpdate,
    db: Session = Depends(get_db),
    analista: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    proyecto = _cargar_proyecto(
        db,
        proyecto_id,
    )

    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )

    if proyecto.estado == payload.estado:
        estado_texto = (
            "activo"
            if payload.estado
            else "inactivo"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El proyecto ya se encuentra "
                f"{estado_texto}."
            ),
        )

    estado_anterior = proyecto.estado

    proyecto.estado = payload.estado

    auditoria = Audit(
        usuario_id=analista.usuario_id,
        entidad_afectada="PROYECTO",
        registro_id=proyecto.proyecto_id,
        estado_anterior=estado_anterior,
        estado_nuevo=payload.estado,
    )

    db.add(auditoria)

    try:
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No fue posible actualizar "
                "el estado del proyecto."
            ),
        ) from None

    proyecto_actualizado = _cargar_proyecto(
        db,
        proyecto_id,
    )

    return _respuesta_proyecto(
        db,
        proyecto_actualizado,
    )


# ============================================================
# CP-04-C07 / C08 / C09
# ACTIVAR / DESACTIVAR MODELO + RF16
# ============================================================

@router.patch(
    "/models/{modelo_id}/estado",
    response_model=DataModelResponse,
)
def cambiar_estado_modelo(
    modelo_id: int,
    payload: DataModelStatusUpdate,
    db: Session = Depends(get_db),
    analista: User = Depends(
        require_roles("Analista/Tester")
    ),
):
    modelo = _cargar_modelo(
        db,
        modelo_id,
    )

    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo no encontrado.",
        )

    if modelo.estado == payload.estado:
        estado_texto = (
            "activo"
            if payload.estado
            else "inactivo"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El modelo ya se encuentra "
                f"{estado_texto}."
            ),
        )

    proyecto = _cargar_proyecto(
        db,
        modelo.proyecto_id,
    )

    if (
        payload.estado
        and proyecto is not None
        and not proyecto.estado
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se puede activar un modelo "
                "perteneciente a un proyecto inactivo."
            ),
        )

    estado_anterior = modelo.estado

    modelo.estado = payload.estado

    auditoria = Audit(
        usuario_id=analista.usuario_id,
        entidad_afectada="MODELO",
        registro_id=modelo.modelo_id,
        estado_anterior=estado_anterior,
        estado_nuevo=payload.estado,
    )

    db.add(auditoria)

    try:
        db.commit()
        db.refresh(modelo)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No fue posible actualizar "
                "el estado del modelo."
            ),
        ) from None

    return modelo