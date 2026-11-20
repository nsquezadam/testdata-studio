from __future__ import annotations

# ============================================================
# VERIFICACIÓN 2026-11-20 - ROUTER CAMPOS Y REGLAS
# Este archivo expone los endpoints de catálogos, campos y reglas.
# Motivo: confirmar que el router configuration conserve sus 11 rutas
# durante la integración con M03 y evitar respuestas 404 por versiones mezcladas.
# ============================================================

# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-04 v5 / CONDITIONAL GENERAL
# Se redefine CONDITIONAL como una regla simple SI/ENTONCES:
# - un campo CONDICION evalúa una condición contra un valor;
# - un campo PRINCIPAL recibe una consecuencia configurable.
# Motivo: evitar que CONDITIONAL quede limitado únicamente a
# obligatoriedad condicional y diferenciarlo de COMPARISON.
# Se mantiene el alcance MVP: una condición + una consecuencia,
# sin combinaciones múltiples AND/OR.
# ============================================================

# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-03 / CATÁLOGOS M02
# Los endpoints /data-types y /rule-types vuelven a exponer los nombres
# de identificador específicos del modelo (tipo_dato_id / tipo_regla_id).
# Motivo: al responder solo "id", el frontend recibía undefined en los
# <option>, generando warning de key y enviando tipo_dato_id=null (422).
# ============================================================


# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-02
# Se valida que el orden de un campo sea único dentro del mismo modelo.
# La validación se aplica tanto al crear como al modificar campos para
# evitar configuraciones ambiguas en M02.
# Motivo: durante CP-05 Frontend se detectó que dos campos podían quedar
# con el mismo valor de orden.
# ============================================================

from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db import get_db
from app.models.audit import Audit
from app.models.configuration import (
    BusinessRule,
    DataField,
    DataType,
    RuleField,
    RuleParameter,
    RuleType,
)
from app.models.project import DataModel, Project
from app.models.user import User
from app.schemas.configuration import (
    BusinessRuleCreate,
    BusinessRuleResponse,
    BusinessRuleStatusUpdate,
    BusinessRuleUpdate,
    CatalogResponse,
    DataTypeCatalogResponse,
    RuleTypeCatalogResponse,
    DataFieldCreate,
    DataFieldResponse,
    DataFieldStatusUpdate,
    DataFieldUpdate,
    RuleFieldResponse,
    RuleParameterResponse,
)


router = APIRouter(tags=["Campos y reglas"])

ALLOWED_FIELD_ROLES = {"PRINCIPAL", "REFERENCIA", "CONDICION"}
ALLOWED_OPERATORS = {"=", "!=", ">", ">=", "<", "<="}
CONDITIONAL_ACTIONS = {
    "REQUIRED",
    "EQUALS",
    "NOT_EQUALS",
    "GREATER_THAN",
    "GREATER_EQUAL",
    "LESS_THAN",
    "LESS_EQUAL",
    "ALLOWED_VALUES",
}
CONDITIONAL_ORDER_ACTIONS = {
    "GREATER_THAN",
    "GREATER_EQUAL",
    "LESS_THAN",
    "LESS_EQUAL",
}



# ============================================================
# FUNCIONES AUXILIARES
# ============================================================


def _limpiar_texto(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def _cargar_modelo(db: Session, modelo_id: int) -> DataModel | None:
    return db.scalar(
        select(DataModel).where(DataModel.modelo_id == modelo_id)
    )


def _validar_modelo_configurable(db: Session, modelo_id: int) -> DataModel:
    modelo = _cargar_modelo(db, modelo_id)

    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo no encontrado.",
        )

    proyecto = db.scalar(
        select(Project).where(Project.proyecto_id == modelo.proyecto_id)
    )

    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto asociado no encontrado.",
        )

    if not proyecto.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar la configuración de un proyecto inactivo.",
        )

    if not modelo.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar la configuración de un modelo inactivo.",
        )

    return modelo


def _cargar_campo(db: Session, campo_id: int) -> DataField | None:
    return db.scalar(
        select(DataField).where(DataField.campo_id == campo_id)
    )


def _validar_orden_campo_disponible(
    db: Session,
    modelo_id: int,
    orden: int | None,
    campo_id_excluir: int | None = None,
) -> None:
    if orden is None:
        return

    condiciones = [
        DataField.modelo_id == modelo_id,
        DataField.orden == orden,
    ]

    if campo_id_excluir is not None:
        condiciones.append(DataField.campo_id != campo_id_excluir)

    existente = db.scalar(
        select(DataField).where(*condiciones)
    )

    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El orden {orden} ya está asignado al campo "
                f"'{existente.nombre}' dentro del modelo. "
                "Seleccione otro orden."
            ),
        )


def _cargar_regla(db: Session, regla_id: int) -> BusinessRule | None:
    return db.scalar(
        select(BusinessRule).where(BusinessRule.regla_id == regla_id)
    )


def _respuesta_campo(db: Session, campo: DataField) -> DataFieldResponse:
    tipo = db.scalar(
        select(DataType).where(DataType.tipo_dato_id == campo.tipo_dato_id)
    )

    if tipo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El campo posee un tipo de dato no disponible.",
        )

    return DataFieldResponse(
        campo_id=campo.campo_id,
        modelo_id=campo.modelo_id,
        tipo_dato_id=campo.tipo_dato_id,
        tipo_dato_codigo=tipo.codigo,
        tipo_dato_nombre=tipo.nombre,
        nombre=campo.nombre,
        descripcion=campo.descripcion,
        orden=campo.orden,
        estado=campo.estado,
    )


def _respuesta_regla(db: Session, regla: BusinessRule) -> BusinessRuleResponse:
    tipo = db.scalar(
        select(RuleType).where(RuleType.tipo_regla_id == regla.tipo_regla_id)
    )

    if tipo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La regla posee un tipo no disponible.",
        )

    asociaciones = db.execute(
        select(RuleField, DataField, DataType)
        .join(DataField, DataField.campo_id == RuleField.campo_id)
        .join(DataType, DataType.tipo_dato_id == DataField.tipo_dato_id)
        .where(RuleField.regla_id == regla.regla_id)
        .order_by(RuleField.campo_id)
    ).all()

    parametros = db.scalars(
        select(RuleParameter)
        .where(RuleParameter.regla_id == regla.regla_id)
        .order_by(
            RuleParameter.orden.is_(None),
            RuleParameter.orden,
            RuleParameter.parametro_id,
        )
    ).all()

    return BusinessRuleResponse(
        regla_id=regla.regla_id,
        modelo_id=regla.modelo_id,
        tipo_regla_id=regla.tipo_regla_id,
        tipo_regla_codigo=tipo.codigo,
        tipo_regla_nombre=tipo.nombre,
        nombre=regla.nombre,
        descripcion=regla.descripcion,
        estado=regla.estado,
        fecha_creacion=regla.fecha_creacion,
        campos=[
            RuleFieldResponse(
                campo_id=campo.campo_id,
                campo_nombre=campo.nombre,
                tipo_dato_codigo=tipo_dato.codigo,
                rol_campo=asociacion.rol_campo,
            )
            for asociacion, campo, tipo_dato in asociaciones
        ],
        parametros=[
            RuleParameterResponse(
                parametro_id=parametro.parametro_id,
                clave=parametro.clave,
                valor=parametro.valor,
                orden=parametro.orden,
            )
            for parametro in parametros
        ],
    )


def _parametros_dict(parametros) -> dict[str, str]:
    resultado: dict[str, str] = {}

    for parametro in parametros:
        clave = parametro.clave.strip().lower()
        valor = parametro.valor.strip()

        if clave in resultado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El parámetro '{clave}' se encuentra repetido.",
            )

        resultado[clave] = valor

    return resultado


def _validar_roles_campos(campos) -> list[tuple[int, str]]:
    resultado: list[tuple[int, str]] = []
    campos_repetidos: set[int] = set()

    for item in campos:
        rol = item.rol_campo.strip().upper()

        if rol not in ALLOWED_FIELD_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "El rol del campo debe ser PRINCIPAL, REFERENCIA o CONDICION."
                ),
            )

        if item.campo_id in campos_repetidos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un mismo campo no puede asociarse más de una vez a la regla.",
            )

        campos_repetidos.add(item.campo_id)
        resultado.append((item.campo_id, rol))

    return resultado


def _cargar_campos_regla(
    db: Session,
    modelo_id: int,
    campos_normalizados: list[tuple[int, str]],
) -> dict[int, tuple[DataField, DataType]]:
    resultado: dict[int, tuple[DataField, DataType]] = {}

    for campo_id, _ in campos_normalizados:
        fila = db.execute(
            select(DataField, DataType)
            .join(DataType, DataType.tipo_dato_id == DataField.tipo_dato_id)
            .where(DataField.campo_id == campo_id)
        ).first()

        if fila is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El campo {campo_id} no existe.",
            )

        campo, tipo_dato = fila

        if campo.modelo_id != modelo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Todos los campos asociados deben pertenecer al mismo modelo de la regla."
                ),
            )

        if not campo.estado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El campo '{campo.nombre}' se encuentra inactivo.",
            )

        if not tipo_dato.estado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El tipo de dato del campo '{campo.nombre}' se encuentra inactivo.",
            )

        resultado[campo_id] = (campo, tipo_dato)

    return resultado


def _validar_claves(
    parametros: dict[str, str],
    permitidas: set[str],
    requeridas: set[str],
) -> None:
    faltantes = requeridas - parametros.keys()
    extras = parametros.keys() - permitidas

    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Faltan parámetros requeridos: "
                + ", ".join(sorted(faltantes))
                + "."
            ),
        )

    if extras:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Parámetros no válidos para este tipo de regla: "
                + ", ".join(sorted(extras))
                + "."
            ),
        )


def _valor_comparable(valor: str, tipo_codigo: str):
    if tipo_codigo in {"INTEGER", "DECIMAL"}:
        try:
            return Decimal(valor)
        except InvalidOperation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los valores mínimo y máximo deben ser numéricos.",
            ) from None

    if tipo_codigo == "DATE":
        try:
            return date.fromisoformat(valor)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las fechas deben utilizar el formato AAAA-MM-DD.",
            ) from None

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="La regla de rango solo puede utilizarse con Entero, Decimal o Fecha.",
    )


def _tipos_compatibles(tipo_a: str, tipo_b: str) -> bool:
    if tipo_a == tipo_b:
        return True
    return {tipo_a, tipo_b} <= {"INTEGER", "DECIMAL"}



def _operadores_permitidos_para_tipo(tipo_codigo: str) -> set[str]:
    tipo = tipo_codigo.upper()
    if tipo in {"STRING", "EMAIL", "BOOLEAN"}:
        return {"=", "!="}
    return ALLOWED_OPERATORS


def _validar_valor_para_tipo(valor: str, tipo_codigo: str, etiqueta: str) -> None:
    tipo = tipo_codigo.upper()

    if tipo == "INTEGER":
        try:
            int(valor)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"{etiqueta} debe ser un número entero.",
            ) from None
        return

    if tipo == "DECIMAL":
        try:
            Decimal(valor)
        except InvalidOperation:
            raise HTTPException(
                status_code=400,
                detail=f"{etiqueta} debe ser un número decimal válido.",
            ) from None
        return

    if tipo == "DATE":
        try:
            date.fromisoformat(valor)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"{etiqueta} debe utilizar el formato AAAA-MM-DD.",
            ) from None
        return

    if tipo == "BOOLEAN":
        if valor.strip().lower() not in {"true", "false", "1", "0", "si", "sí", "no"}:
            raise HTTPException(
                status_code=400,
                detail=f"{etiqueta} debe ser un valor booleano válido.",
            )


def _campo_por_rol(
    campos_normalizados: list[tuple[int, str]],
    rol_buscado: str,
) -> int:
    for campo_id, rol in campos_normalizados:
        if rol == rol_buscado:
            return campo_id
    raise HTTPException(status_code=400, detail=f"Falta el campo con rol {rol_buscado}.")


def _validar_configuracion_regla(
    tipo_codigo: str,
    campos_normalizados: list[tuple[int, str]],
    campos_db: dict[int, tuple[DataField, DataType]],
    parametros: dict[str, str],
) -> None:
    codigo = tipo_codigo.upper()
    roles = [rol for _, rol in campos_normalizados]

    if codigo == "REQUIRED":
        if len(campos_normalizados) != 1:
            raise HTTPException(
                status_code=400,
                detail="La regla de obligatoriedad requiere exactamente un campo.",
            )
        _validar_claves(parametros, set(), set())
        return

    if codigo == "RANGE":
        if len(campos_normalizados) != 1:
            raise HTTPException(
                status_code=400,
                detail="La regla de rango requiere exactamente un campo.",
            )
        _validar_claves(parametros, {"min", "max"}, {"min", "max"})
        campo_id = campos_normalizados[0][0]
        tipo = campos_db[campo_id][1].codigo.upper()
        minimo = _valor_comparable(parametros["min"], tipo)
        maximo = _valor_comparable(parametros["max"], tipo)
        if minimo > maximo:
            raise HTTPException(
                status_code=400,
                detail="El valor mínimo no puede ser mayor que el valor máximo.",
            )
        return

    if codigo == "ALLOWED_VALUES":
        if len(campos_normalizados) != 1:
            raise HTTPException(
                status_code=400,
                detail="La regla de valores permitidos requiere exactamente un campo.",
            )
        _validar_claves(parametros, {"valores"}, {"valores"})
        valores = [v.strip() for v in parametros["valores"].split(",") if v.strip()]
        if not valores:
            raise HTTPException(
                status_code=400,
                detail="Debe informar al menos un valor permitido.",
            )
        return

    if codigo == "FORMAT":
        if len(campos_normalizados) != 1:
            raise HTTPException(
                status_code=400,
                detail="La regla de formato/longitud requiere exactamente un campo.",
            )
        campo_id = campos_normalizados[0][0]
        tipo = campos_db[campo_id][1].codigo.upper()
        if tipo not in {"STRING", "EMAIL"}:
            raise HTTPException(
                status_code=400,
                detail="La regla de formato/longitud solo puede utilizarse con Texto o Correo.",
            )
        permitidas = {"patron", "longitud_min", "longitud_max"}
        _validar_claves(parametros, permitidas, set())
        if not parametros:
            raise HTTPException(
                status_code=400,
                detail="Debe informar patrón y/o límites de longitud.",
            )

        long_min = parametros.get("longitud_min")
        long_max = parametros.get("longitud_max")
        try:
            min_num = int(long_min) if long_min is not None else None
            max_num = int(long_max) if long_max is not None else None
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Las longitudes deben ser números enteros.",
            ) from None

        if min_num is not None and min_num < 0:
            raise HTTPException(status_code=400, detail="La longitud mínima no puede ser negativa.")
        if max_num is not None and max_num < 0:
            raise HTTPException(status_code=400, detail="La longitud máxima no puede ser negativa.")
        if min_num is not None and max_num is not None and min_num > max_num:
            raise HTTPException(
                status_code=400,
                detail="La longitud mínima no puede ser mayor que la longitud máxima.",
            )
        return

    if codigo == "COMPARISON":
        if len(campos_normalizados) != 2:
            raise HTTPException(
                status_code=400,
                detail="La comparación entre campos requiere exactamente dos campos.",
            )
        if set(roles) != {"PRINCIPAL", "REFERENCIA"}:
            raise HTTPException(
                status_code=400,
                detail="La comparación requiere un campo PRINCIPAL y uno REFERENCIA.",
            )
        _validar_claves(parametros, {"operador"}, {"operador"})
        if parametros["operador"] not in ALLOWED_OPERATORS:
            raise HTTPException(status_code=400, detail="El operador de comparación no es válido.")

        tipos = [campos_db[campo_id][1].codigo.upper() for campo_id, _ in campos_normalizados]
        if not _tipos_compatibles(tipos[0], tipos[1]):
            raise HTTPException(
                status_code=400,
                detail="Los campos seleccionados no poseen tipos compatibles para comparación.",
            )
        return

    if codigo == "CONDITIONAL":
        if len(campos_normalizados) != 2:
            raise HTTPException(
                status_code=400,
                detail="La condición simple requiere dos campos distintos: CONDICION y PRINCIPAL.",
            )
        if set(roles) != {"PRINCIPAL", "CONDICION"}:
            raise HTTPException(
                status_code=400,
                detail="La condición simple requiere un campo CONDICION y un campo PRINCIPAL.",
            )

        requeridas_base = {"condicion_operador", "condicion_valor", "accion"}
        permitidas = requeridas_base | {"accion_valor", "accion_valores"}
        _validar_claves(parametros, permitidas, requeridas_base)

        condicion_id = _campo_por_rol(campos_normalizados, "CONDICION")
        principal_id = _campo_por_rol(campos_normalizados, "PRINCIPAL")
        condicion_tipo = campos_db[condicion_id][1].codigo.upper()
        principal_tipo = campos_db[principal_id][1].codigo.upper()

        operador = parametros["condicion_operador"]
        if operador not in _operadores_permitidos_para_tipo(condicion_tipo):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El operador '{operador}' no es válido para el tipo "
                    f"{condicion_tipo} del campo condición."
                ),
            )

        _validar_valor_para_tipo(
            parametros["condicion_valor"],
            condicion_tipo,
            "El valor de la condición",
        )

        accion = parametros["accion"].upper()
        if accion not in CONDITIONAL_ACTIONS:
            raise HTTPException(
                status_code=400,
                detail="La acción configurada para la consecuencia no está soportada.",
            )

        if accion == "REQUIRED":
            if "accion_valor" in parametros or "accion_valores" in parametros:
                raise HTTPException(
                    status_code=400,
                    detail="La acción REQUIRED no debe incluir un valor de consecuencia.",
                )
            return

        if accion == "ALLOWED_VALUES":
            if "accion_valores" not in parametros:
                raise HTTPException(
                    status_code=400,
                    detail="La acción ALLOWED_VALUES requiere informar valores permitidos.",
                )
            if "accion_valor" in parametros:
                raise HTTPException(
                    status_code=400,
                    detail="ALLOWED_VALUES utiliza accion_valores, no accion_valor.",
                )
            valores = [v.strip() for v in parametros["accion_valores"].split(",") if v.strip()]
            if not valores:
                raise HTTPException(
                    status_code=400,
                    detail="Debe informar al menos un valor permitido para la consecuencia.",
                )
            for valor in valores:
                _validar_valor_para_tipo(
                    valor,
                    principal_tipo,
                    "Cada valor permitido de la consecuencia",
                )
            return

        if "accion_valor" not in parametros:
            raise HTTPException(
                status_code=400,
                detail=f"La acción {accion} requiere un valor de consecuencia.",
            )
        if "accion_valores" in parametros:
            raise HTTPException(
                status_code=400,
                detail=f"La acción {accion} no utiliza una lista de valores.",
            )

        if accion in CONDITIONAL_ORDER_ACTIONS and principal_tipo not in {"INTEGER", "DECIMAL", "DATE"}:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"La acción {accion} solo puede aplicarse a campos Entero, Decimal o Fecha."
                ),
            )

        _validar_valor_para_tipo(
            parametros["accion_valor"],
            principal_tipo,
            "El valor de la consecuencia",
        )
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="El tipo de regla seleccionado no está soportado por el MVP.",
    )


def _preparar_configuracion_regla(db: Session, modelo_id: int, payload):
    tipo_regla = db.scalar(
        select(RuleType).where(RuleType.tipo_regla_id == payload.tipo_regla_id)
    )

    if tipo_regla is None:
        raise HTTPException(status_code=400, detail="El tipo de regla seleccionado no existe.")
    if not tipo_regla.estado:
        raise HTTPException(status_code=400, detail="El tipo de regla seleccionado se encuentra inactivo.")

    campos_normalizados = _validar_roles_campos(payload.campos)
    campos_db = _cargar_campos_regla(db, modelo_id, campos_normalizados)
    parametros = _parametros_dict(payload.parametros)

    _validar_configuracion_regla(
        tipo_regla.codigo,
        campos_normalizados,
        campos_db,
        parametros,
    )

    return tipo_regla, campos_normalizados


# ============================================================
# CATÁLOGOS
# ============================================================


@router.get("/data-types", response_model=list[DataTypeCatalogResponse])
def listar_tipos_dato(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    tipos = db.scalars(
        select(DataType).where(DataType.estado.is_(True)).order_by(DataType.tipo_dato_id)
    ).all()

    return [
        DataTypeCatalogResponse(
            tipo_dato_id=tipo.tipo_dato_id,
            codigo=tipo.codigo,
            nombre=tipo.nombre,
            descripcion=tipo.descripcion,
            estado=tipo.estado,
        )
        for tipo in tipos
    ]


@router.get("/rule-types", response_model=list[RuleTypeCatalogResponse])
def listar_tipos_regla(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    tipos = db.scalars(
        select(RuleType).where(RuleType.estado.is_(True)).order_by(RuleType.tipo_regla_id)
    ).all()

    return [
        RuleTypeCatalogResponse(
            tipo_regla_id=tipo.tipo_regla_id,
            codigo=tipo.codigo,
            nombre=tipo.nombre,
            descripcion=tipo.descripcion,
            estado=tipo.estado,
        )
        for tipo in tipos
    ]


# ============================================================
# CAMPOS - RF04 / RF16
# ============================================================


@router.get("/models/{modelo_id}/fields", response_model=list[DataFieldResponse])
def listar_campos(
    modelo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    modelo = _cargar_modelo(db, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado.")

    campos = db.scalars(
        select(DataField)
        .where(DataField.modelo_id == modelo_id)
        .order_by(DataField.orden.is_(None), DataField.orden, DataField.campo_id)
    ).all()

    return [_respuesta_campo(db, campo) for campo in campos]


@router.post(
    "/models/{modelo_id}/fields",
    response_model=DataFieldResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_campo(
    modelo_id: int,
    payload: DataFieldCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    _validar_modelo_configurable(db, modelo_id)

    tipo = db.scalar(select(DataType).where(DataType.tipo_dato_id == payload.tipo_dato_id))
    if tipo is None:
        raise HTTPException(status_code=400, detail="El tipo de dato seleccionado no existe.")
    if not tipo.estado:
        raise HTTPException(status_code=400, detail="El tipo de dato seleccionado se encuentra inactivo.")

    nombre = payload.nombre.strip()
    existente = db.scalar(
        select(DataField).where(
            DataField.modelo_id == modelo_id,
            func.lower(DataField.nombre) == nombre.lower(),
        )
    )
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un campo con ese nombre dentro del modelo.",
        )

    _validar_orden_campo_disponible(
        db,
        modelo_id=modelo_id,
        orden=payload.orden,
    )

    campo = DataField(
        modelo_id=modelo_id,
        tipo_dato_id=payload.tipo_dato_id,
        nombre=nombre,
        descripcion=_limpiar_texto(payload.descripcion),
        orden=payload.orden,
        estado=True,
    )
    db.add(campo)

    try:
        db.commit()
        db.refresh(campo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible crear el campo.") from None

    return _respuesta_campo(db, campo)


@router.put("/fields/{campo_id}", response_model=DataFieldResponse)
def modificar_campo(
    campo_id: int,
    payload: DataFieldUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    campo = _cargar_campo(db, campo_id)
    if campo is None:
        raise HTTPException(status_code=404, detail="Campo no encontrado.")

    _validar_modelo_configurable(db, campo.modelo_id)

    tipo = db.scalar(select(DataType).where(DataType.tipo_dato_id == payload.tipo_dato_id))
    if tipo is None or not tipo.estado:
        raise HTTPException(status_code=400, detail="El tipo de dato seleccionado no se encuentra disponible.")

    nombre = payload.nombre.strip()
    existente = db.scalar(
        select(DataField).where(
            DataField.modelo_id == campo.modelo_id,
            func.lower(DataField.nombre) == nombre.lower(),
            DataField.campo_id != campo_id,
        )
    )
    if existente is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe otro campo con ese nombre dentro del modelo.",
        )

    _validar_orden_campo_disponible(
        db,
        modelo_id=campo.modelo_id,
        orden=payload.orden,
        campo_id_excluir=campo_id,
    )

    campo.tipo_dato_id = payload.tipo_dato_id
    campo.nombre = nombre
    campo.descripcion = _limpiar_texto(payload.descripcion)
    campo.orden = payload.orden

    try:
        db.commit()
        db.refresh(campo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible modificar el campo.") from None

    return _respuesta_campo(db, campo)


@router.patch("/fields/{campo_id}/estado", response_model=DataFieldResponse)
def cambiar_estado_campo(
    campo_id: int,
    payload: DataFieldStatusUpdate,
    db: Session = Depends(get_db),
    analista: User = Depends(require_roles("Analista/Tester")),
):
    campo = _cargar_campo(db, campo_id)
    if campo is None:
        raise HTTPException(status_code=404, detail="Campo no encontrado.")

    if campo.estado == payload.estado:
        estado_texto = "activo" if payload.estado else "inactivo"
        raise HTTPException(status_code=400, detail=f"El campo ya se encuentra {estado_texto}.")

    if payload.estado:
        _validar_modelo_configurable(db, campo.modelo_id)
    else:
        regla_activa = db.scalar(
            select(BusinessRule)
            .join(RuleField, RuleField.regla_id == BusinessRule.regla_id)
            .where(
                RuleField.campo_id == campo_id,
                BusinessRule.estado.is_(True),
            )
        )
        if regla_activa is not None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El campo está asociado a una regla activa. Desactive primero la regla correspondiente."
                ),
            )

    estado_anterior = campo.estado
    campo.estado = payload.estado
    db.add(
        Audit(
            usuario_id=analista.usuario_id,
            entidad_afectada="CAMPO",
            registro_id=campo.campo_id,
            estado_anterior=estado_anterior,
            estado_nuevo=payload.estado,
        )
    )

    try:
        db.commit()
        db.refresh(campo)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="No fue posible actualizar el estado del campo.") from None

    return _respuesta_campo(db, campo)


# ============================================================
# REGLAS - RF05 / RF06 / RF07 / RF16
# ============================================================


@router.get("/models/{modelo_id}/rules", response_model=list[BusinessRuleResponse])
def listar_reglas(
    modelo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    modelo = _cargar_modelo(db, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado.")

    reglas = db.scalars(
        select(BusinessRule)
        .where(BusinessRule.modelo_id == modelo_id)
        .order_by(BusinessRule.regla_id)
    ).all()

    return [_respuesta_regla(db, regla) for regla in reglas]


@router.get("/rules/{regla_id}", response_model=BusinessRuleResponse)
def consultar_regla(
    regla_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    regla = _cargar_regla(db, regla_id)
    if regla is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada.")
    return _respuesta_regla(db, regla)


@router.post(
    "/models/{modelo_id}/rules",
    response_model=BusinessRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_regla(
    modelo_id: int,
    payload: BusinessRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    _validar_modelo_configurable(db, modelo_id)
    _, campos_normalizados = _preparar_configuracion_regla(db, modelo_id, payload)

    nombre = payload.nombre.strip()
    existente = db.scalar(
        select(BusinessRule).where(
            BusinessRule.modelo_id == modelo_id,
            func.lower(BusinessRule.nombre) == nombre.lower(),
        )
    )
    if existente is not None:
        raise HTTPException(status_code=409, detail="Ya existe una regla con ese nombre dentro del modelo.")

    regla = BusinessRule(
        modelo_id=modelo_id,
        tipo_regla_id=payload.tipo_regla_id,
        nombre=nombre,
        descripcion=_limpiar_texto(payload.descripcion),
        estado=True,
    )
    db.add(regla)

    try:
        db.flush()

        for campo_id, rol in campos_normalizados:
            db.add(RuleField(regla_id=regla.regla_id, campo_id=campo_id, rol_campo=rol))

        for parametro in payload.parametros:
            db.add(
                RuleParameter(
                    regla_id=regla.regla_id,
                    clave=parametro.clave.strip().lower(),
                    valor=parametro.valor.strip(),
                    orden=parametro.orden,
                )
            )

        db.commit()
        db.refresh(regla)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible crear la regla.") from None

    return _respuesta_regla(db, regla)


@router.put("/rules/{regla_id}", response_model=BusinessRuleResponse)
def modificar_regla(
    regla_id: int,
    payload: BusinessRuleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Analista/Tester")),
):
    regla = _cargar_regla(db, regla_id)
    if regla is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada.")

    _validar_modelo_configurable(db, regla.modelo_id)
    _, campos_normalizados = _preparar_configuracion_regla(db, regla.modelo_id, payload)

    nombre = payload.nombre.strip()
    existente = db.scalar(
        select(BusinessRule).where(
            BusinessRule.modelo_id == regla.modelo_id,
            func.lower(BusinessRule.nombre) == nombre.lower(),
            BusinessRule.regla_id != regla_id,
        )
    )
    if existente is not None:
        raise HTTPException(status_code=409, detail="Ya existe otra regla con ese nombre dentro del modelo.")

    regla.tipo_regla_id = payload.tipo_regla_id
    regla.nombre = nombre
    regla.descripcion = _limpiar_texto(payload.descripcion)

    try:
        db.execute(delete(RuleField).where(RuleField.regla_id == regla_id))
        db.execute(delete(RuleParameter).where(RuleParameter.regla_id == regla_id))

        for campo_id, rol in campos_normalizados:
            db.add(RuleField(regla_id=regla_id, campo_id=campo_id, rol_campo=rol))

        for parametro in payload.parametros:
            db.add(
                RuleParameter(
                    regla_id=regla_id,
                    clave=parametro.clave.strip().lower(),
                    valor=parametro.valor.strip(),
                    orden=parametro.orden,
                )
            )

        db.commit()
        db.refresh(regla)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible modificar la regla.") from None

    return _respuesta_regla(db, regla)


@router.patch("/rules/{regla_id}/estado", response_model=BusinessRuleResponse)
def cambiar_estado_regla(
    regla_id: int,
    payload: BusinessRuleStatusUpdate,
    db: Session = Depends(get_db),
    analista: User = Depends(require_roles("Analista/Tester")),
):
    regla = _cargar_regla(db, regla_id)
    if regla is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada.")

    if regla.estado == payload.estado:
        estado_texto = "activa" if payload.estado else "inactiva"
        raise HTTPException(status_code=400, detail=f"La regla ya se encuentra {estado_texto}.")

    if payload.estado:
        _validar_modelo_configurable(db, regla.modelo_id)

        campos_inactivos = db.scalars(
            select(DataField)
            .join(RuleField, RuleField.campo_id == DataField.campo_id)
            .where(
                RuleField.regla_id == regla_id,
                DataField.estado.is_(False),
            )
        ).all()

        if campos_inactivos:
            raise HTTPException(
                status_code=400,
                detail="No se puede activar una regla que utiliza campos inactivos.",
            )

    estado_anterior = regla.estado
    regla.estado = payload.estado
    db.add(
        Audit(
            usuario_id=analista.usuario_id,
            entidad_afectada="REGLA",
            registro_id=regla.regla_id,
            estado_anterior=estado_anterior,
            estado_nuevo=payload.estado,
        )
    )

    try:
        db.commit()
        db.refresh(regla)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="No fue posible actualizar el estado de la regla.") from None

    return _respuesta_regla(db, regla)
