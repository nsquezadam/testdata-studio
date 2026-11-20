# ============================================================
# MODIFICACIÓN 2026-11-18 - INC-02 / compatibilidad M02
# Se unifican los nombres actuales de los modelos de configuración y se
# exponen alias compatibles con la primera versión de M02.
# Motivo: evitar ImportError cuando una carpeta local contiene archivos
# de dos versiones distintas (FieldDefinition/Rule vs DataField/BusinessRule).
# ============================================================

from app.models.audit import Audit
from app.models.configuration import (
    BusinessRule,
    DataField,
    DataType,
    FieldDefinition,
    Rule,
    RuleField,
    RuleParameter,
    RuleType,
)
from app.models.project import DataModel, Project

# MODIFICACIÓN 2026-11-18 - M03 / CP-06
# Se exponen los modelos de persistencia de generación y trazabilidad.
from app.models.generation import CaseRule, GeneratedData, Generation, TestCase
from app.models.user import Role, User


__all__ = [
    "Role",
    "User",
    "Audit",
    "Project",
    "DataModel",
    "DataType",
    "DataField",
    "FieldDefinition",
    "RuleType",
    "BusinessRule",
    "Rule",
    "RuleField",
    "RuleParameter",
    "Generation",
    "TestCase",
    "CaseRule",
    "GeneratedData",
]
