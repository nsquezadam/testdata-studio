/* ============================================================
   MODIFICACIÓN 2026-11-18 - M02 / INC-02 / INC-03
   INC-02: validación preventiva para no enviar un orden ya utilizado por
   otro campo del mismo modelo. El backend mantiene la validación definitiva.
   INC-03: normalización de IDs de catálogos. Se acepta tanto el contrato
   actual (tipo_dato_id / tipo_regla_id) como el formato transitorio "id".
   Motivo: evitar key indefinida en <option> y payload tipo_dato_id=null,
   que generaba warning de React y respuesta 422 al crear un campo.
   ============================================================ */

/* ============================================================
   MODIFICACIÓN 2026-11-18 - INC-04 v5 / CONDITIONAL GENERAL
   Se redefine CONDITIONAL como una regla SI/ENTONCES con una condición
   y una consecuencia configurable sobre otro campo. COMPARISON queda
   claramente separado como Campo principal operador Campo referencia.
   Motivo: evitar que la regla condicional quede limitada únicamente a
   obligatoriedad y mejorar claridad funcional para usuario y defensa.
   ============================================================ */

/* ============================================================
   MODIFICACIÓN 2026-11-19 - M02/M03 - AJUSTES DE CONTINUIDAD Y UX
   1) La carga de proyectos deja de depender de los catálogos. Si falla
      data-types o rule-types, la configuración existente sigue visible.
   2) Los formularios de campo y regla se desplazan automáticamente al
      abrirse para evitar que el usuario tenga que buscarlos en la página.
   3) Se retiran identificadores internos de documentación de los títulos
      visibles; se mantienen únicamente en comentarios técnicos.
   Motivo: mejorar continuidad operativa y experiencia de uso durante CP-06.
   ============================================================ */

/* ============================================================
   MODIFICACIÓN 2026-11-20 - CONFIGURACIÓN / MANEJO PARCIAL DE ERRORES
   La carga de campos y reglas se realiza de forma independiente.
   Motivo: evitar que un fallo 404 en una ruta elimine también la
   información que sí pudo recuperarse y reemplazar el mensaje técnico
   "Not Found" por una respuesta funcional para el usuario.
   ============================================================ */

import { useEffect, useMemo, useRef, useState } from 'react'

import {
  getProjects,
  getProjectModels,
} from '../api/projects'

import {
  getDataTypes,
  getRuleTypes,
  getFieldsByModel,
  createField,
  updateField,
  changeFieldStatus,
  getRulesByModel,
  createRule,
  updateRule,
  changeRuleStatus,
} from '../api/configuration'


const initialFieldForm = {
  tipo_dato_id: '',
  nombre: '',
  descripcion: '',
  orden: '',
}


const initialRuleForm = {
  tipo_regla_id: '',
  nombre: '',
  descripcion: '',
  campo_principal_id: '',
  campo_referencia_id: '',
  campo_condicion_id: '',
  comparacion_operador: '=',
  condicion_operador: '=',
  condicion_valor: '',
  accion_condicional: '',
  accion_valor: '',
  accion_valores: '',
  min: '',
  max: '',
  valores: '',
  patron: '',
  longitud_min: '',
  longitud_max: '',
}


function normalizeDataTypes(items = []) {
  return items.map((item) => ({
    ...item,
    tipo_dato_id: item.tipo_dato_id ?? item.id,
  }))
}


function normalizeRuleTypes(items = []) {
  return items.map((item) => ({
    ...item,
    tipo_regla_id: item.tipo_regla_id ?? item.id,
  }))
}


function normalizeAllowedValues(value) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
}


function parameterMap(rule) {
  const map = {}

  for (const parameter of rule?.parametros || []) {
    if (parameter.clave === 'valor') {
      if (!map.valor) {
        map.valor = []
      }
      map.valor.push(parameter.valor)
    } else {
      map[parameter.clave] = parameter.valor
    }
  }

  return map
}


const CONDITIONAL_ACTIONS = [
  { value: 'REQUIRED', label: 'Obligatorio' },
  { value: 'EQUALS', label: 'Igual a (=)' },
  { value: 'NOT_EQUALS', label: 'Distinto de (!=)' },
  { value: 'GREATER_THAN', label: 'Mayor que (>)', ordered: true },
  { value: 'GREATER_EQUAL', label: 'Mayor o igual (>=)', ordered: true },
  { value: 'LESS_THAN', label: 'Menor que (<)', ordered: true },
  { value: 'LESS_EQUAL', label: 'Menor o igual (<=)', ordered: true },
  { value: 'ALLOWED_VALUES', label: 'Valores permitidos' },
]


function fieldDisplayName(field) {
  return field?.nombre || field?.campo_nombre || ''
}


function operatorsForField(field) {
  const type = field?.tipo_dato_codigo
  if (['STRING', 'EMAIL', 'BOOLEAN'].includes(type)) {
    return ['=', '!=']
  }
  return ['=', '!=', '>', '>=', '<', '<=']
}


function conditionalActionsForField(field) {
  const orderedType = ['INTEGER', 'DECIMAL', 'DATE'].includes(
    field?.tipo_dato_codigo
  )
  return CONDITIONAL_ACTIONS.filter(
    (action) => !action.ordered || orderedType
  )
}


function conditionalActionSymbol(action) {
  return {
    EQUALS: '=',
    NOT_EQUALS: '!=',
    GREATER_THAN: '>',
    GREATER_EQUAL: '>=',
    LESS_THAN: '<',
    LESS_EQUAL: '<=',
  }[action] || ''
}


function fieldByRole(rule, roles) {
  return (rule?.campos || []).find((field) =>
    roles.includes(field.rol_campo)
  )
}


function ruleBusinessSummary(rule) {
  const params = parameterMap(rule)

  if (rule.tipo_regla_codigo === 'COMPARISON') {
    const principal = fieldByRole(rule, ['PRINCIPAL', 'ORIGEN'])
    const reference = fieldByRole(rule, ['REFERENCIA', 'DESTINO'])
    if (principal && reference) {
      return [
        `${fieldDisplayName(principal)} ${params.operador || '?'} ${fieldDisplayName(reference)}`,
      ]
    }
  }

  if (rule.tipo_regla_codigo === 'CONDITIONAL') {
    const condition = fieldByRole(rule, ['CONDICION'])
    const target = fieldByRole(rule, ['PRINCIPAL'])

    if (!params.accion) {
      return ['Configuración heredada: editar para completar SI / ENTONCES']
    }

    const conditionText = `SI ${fieldDisplayName(condition) || '?'} ${params.condicion_operador || '?'} ${params.condicion_valor || '?'}`

    let consequence = ''
    if (params.accion === 'REQUIRED') {
      consequence = `${fieldDisplayName(target) || '?'} es obligatorio`
    } else if (params.accion === 'ALLOWED_VALUES') {
      consequence = `${fieldDisplayName(target) || '?'} pertenece a [${params.accion_valores || ''}]`
    } else {
      consequence = `${fieldDisplayName(target) || '?'} ${conditionalActionSymbol(params.accion)} ${params.accion_valor || '?'}`
    }

    return [conditionText, `ENTONCES ${consequence}`]
  }

  return null
}


export default function CamposRulesPage() {
  const [projects, setProjects] = useState([])
  const [models, setModels] = useState([])
  const [dataTypes, setDataTypes] = useState([])
  const [ruleTypes, setRuleTypes] = useState([])
  const [fields, setFields] = useState([])
  const [rules, setRules] = useState([])

  const [selectedProject, setSelectedProject] = useState(null)
  const [selectedModel, setSelectedModel] = useState(null)

  const [loading, setLoading] = useState(true)
  const [loadingModels, setLoadingModels] = useState(false)
  const [loadingConfiguration, setLoadingConfiguration] = useState(false)
  const [savingField, setSavingField] = useState(false)
  const [savingRule, setSavingRule] = useState(false)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [catalogWarning, setCatalogWarning] = useState('')

  const fieldFormRef = useRef(null)
  const ruleFormRef = useRef(null)

  const [fieldFormOpen, setFieldFormOpen] = useState(false)
  const [editingField, setEditingField] = useState(null)
  const [fieldForm, setFieldForm] = useState(initialFieldForm)

  const [ruleFormOpen, setRuleFormOpen] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [ruleForm, setRuleForm] = useState(initialRuleForm)


  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (fieldFormOpen) {
      requestAnimationFrame(() => {
        fieldFormRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        })
      })
    }
  }, [fieldFormOpen, editingField])

  useEffect(() => {
    if (ruleFormOpen) {
      requestAnimationFrame(() => {
        ruleFormRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        })
      })
    }
  }, [ruleFormOpen, editingRule])


  async function loadInitialData() {
    setLoading(true)
    setError('')
    setCatalogWarning('')

    try {
      // Los proyectos se cargan primero y de forma independiente.
      // Así un fallo puntual de catálogo no deja toda la vista vacía.
      const projectData = await getProjects()
      setProjects(projectData)

      const [dataTypeResult, ruleTypeResult] = await Promise.allSettled([
        getDataTypes(),
        getRuleTypes(),
      ])

      if (dataTypeResult.status === 'fulfilled') {
        setDataTypes(normalizeDataTypes(dataTypeResult.value))
      } else {
        setDataTypes([])
      }

      if (ruleTypeResult.status === 'fulfilled') {
        setRuleTypes(normalizeRuleTypes(ruleTypeResult.value))
      } else {
        setRuleTypes([])
      }

      const unavailableCatalogs = []
      if (dataTypeResult.status === 'rejected') {
        unavailableCatalogs.push('tipos de datos')
      }
      if (ruleTypeResult.status === 'rejected') {
        unavailableCatalogs.push('tipos de reglas')
      }

      if (unavailableCatalogs.length) {
        setCatalogWarning(
          `La configuración existente está disponible, pero no fue posible cargar ${unavailableCatalogs.join(' y ')}. ` +
          'La creación o edición puede quedar limitada hasta restablecer esos catálogos.'
        )
      }

      const firstProject =
        projectData.find((project) => project.estado) ||
        projectData[0] ||
        null

      if (firstProject) {
        await loadModelsForProject(firstProject)
      }

    } catch (err) {
      setProjects([])
      setModels([])
      setSelectedProject(null)
      setSelectedModel(null)
      setError(err.message)

    } finally {
      setLoading(false)
    }
  }

  async function loadModelsForProject(project) {
    setSelectedProject(project)
    setSelectedModel(null)
    setModels([])
    setFields([])
    setRules([])
    setFieldFormOpen(false)
    setRuleFormOpen(false)
    setEditingField(null)
    setEditingRule(null)
    setLoadingModels(true)
    setError('')
    setSuccess('')

    try {
      const modelData =
        await getProjectModels(project.proyecto_id)

      setModels(modelData)

      const firstModel =
        modelData.find((model) => model.estado) ||
        modelData[0] ||
        null

      if (firstModel) {
        setSelectedModel(firstModel)
        await loadConfiguration(firstModel)
      }

    } catch (err) {
      setError(err.message)

    } finally {
      setLoadingModels(false)
    }
  }


  async function loadConfiguration(model) {
    setSelectedModel(model)
    setLoadingConfiguration(true)
    setError('')
    setSuccess('')
    setFieldFormOpen(false)
    setRuleFormOpen(false)
    setEditingField(null)
    setEditingRule(null)

    try {
      const [fieldResult, ruleResult] = await Promise.allSettled([
        getFieldsByModel(model.modelo_id),
        getRulesByModel(model.modelo_id),
      ])

      if (fieldResult.status === 'fulfilled') {
        setFields(fieldResult.value)
      } else {
        setFields([])
      }

      if (ruleResult.status === 'fulfilled') {
        setRules(ruleResult.value)
      } else {
        setRules([])
      }

      const failures = [fieldResult, ruleResult].filter(
        (result) => result.status === 'rejected'
      )

      if (failures.length) {
        const routeUnavailable = failures.some(
          (result) => result.reason?.status === 404
        )

        // El detalle técnico queda en consola para QA/desarrollo.
        console.error(
          'No fue posible cargar completamente la configuración del modelo.',
          failures.map((result) => result.reason)
        )

        setError(
          routeUnavailable
            ? 'No fue posible cargar la configuración de campos y reglas. Verifica que el backend de configuración esté disponible.'
            : 'No fue posible cargar completamente la configuración del modelo.'
        )
      }

    } finally {
      setLoadingConfiguration(false)
    }
  }


  async function handleProjectSelection(event) {
    const projectId = Number(event.target.value)

    const project = projects.find(
      (item) => item.proyecto_id === projectId
    )

    if (project) {
      await loadModelsForProject(project)
    }
  }


  async function handleModelSelection(event) {
    const modelId = Number(event.target.value)

    const model = models.find(
      (item) => item.modelo_id === modelId
    )

    if (model) {
      await loadConfiguration(model)
    }
  }


  const configurationEnabled =
    Boolean(selectedProject?.estado && selectedModel?.estado)


  // ============================================================
  // CAMPOS
  // ============================================================

  function openCreateFieldForm() {
    if (!dataTypes.length) {
      setError(
        'No se encuentran disponibles los tipos de datos. Recarga la pantalla o verifica el catálogo antes de crear un campo.'
      )
      return
    }

    const nextOrder = fields.length
      ? Math.max(...fields.map((field) => Number(field.orden || 0))) + 1
      : 1

    setEditingField(null)
    setFieldForm({
      ...initialFieldForm,
      tipo_dato_id: dataTypes[0]?.tipo_dato_id
        ? String(dataTypes[0].tipo_dato_id)
        : '',
      orden: String(nextOrder),
    })
    setError('')
    setSuccess('')
    setFieldFormOpen(true)
    setRuleFormOpen(false)
  }


  function openEditFieldForm(field) {
    setEditingField(field)
    setFieldForm({
      tipo_dato_id: String(field.tipo_dato_id),
      nombre: field.nombre || '',
      descripcion: field.descripcion || '',
      orden: field.orden == null ? '' : String(field.orden),
    })
    setError('')
    setSuccess('')
    setFieldFormOpen(true)
    setRuleFormOpen(false)
  }


  function closeFieldForm() {
    setFieldFormOpen(false)
    setEditingField(null)
    setFieldForm(initialFieldForm)
    setError('')
  }


  function handleFieldChange(event) {
    const { name, value } = event.target

    setFieldForm((current) => ({
      ...current,
      [name]: value,
    }))
  }


  async function handleFieldSubmit(event) {
    event.preventDefault()

    if (!selectedModel) {
      return
    }

    const selectedOrder = fieldForm.orden
      ? Number(fieldForm.orden)
      : null

    if (selectedOrder != null) {
      const duplicatedOrder = fields.find((field) =>
        Number(field.orden) === selectedOrder &&
        (!editingField || field.campo_id !== editingField.campo_id)
      )

      if (duplicatedOrder) {
        setError(
          `El orden ${selectedOrder} ya está asignado al campo "${duplicatedOrder.nombre}". Seleccione otro orden.`
        )
        setSuccess('')
        return
      }
    }

    setSavingField(true)
    setError('')
    setSuccess('')

    try {
      const payload = {
        tipo_dato_id: Number(fieldForm.tipo_dato_id),
        nombre: fieldForm.nombre.trim(),
        descripcion: fieldForm.descripcion.trim() || null,
        orden: selectedOrder,
      }

      if (editingField) {
        const updated = await updateField(
          editingField.campo_id,
          payload,
        )

        setFields((current) =>
          current.map((field) =>
            field.campo_id === updated.campo_id
              ? updated
              : field
          )
        )

        setSuccess('Campo modificado correctamente.')

      } else {
        const created = await createField(
          selectedModel.modelo_id,
          payload,
        )

        setFields((current) => [
          ...current,
          created,
        ].sort((a, b) =>
          Number(a.orden || 0) - Number(b.orden || 0)
        ))

        setSuccess('Campo creado correctamente.')
      }

      setFieldFormOpen(false)
      setEditingField(null)
      setFieldForm(initialFieldForm)

    } catch (err) {
      setError(err.message)

    } finally {
      setSavingField(false)
    }
  }


  async function handleFieldStatus(field) {
    const newStatus = !field.estado
    const action = newStatus ? 'reactivar' : 'desactivar'

    const confirmed = window.confirm(
      `¿Deseas ${action} el campo "${field.nombre}"?`
    )

    if (!confirmed) {
      return
    }

    setError('')
    setSuccess('')

    try {
      const updated = await changeFieldStatus(
        field.campo_id,
        newStatus,
      )

      setFields((current) =>
        current.map((item) =>
          item.campo_id === updated.campo_id
            ? updated
            : item
        )
      )

      setSuccess(
        newStatus
          ? 'Campo reactivado correctamente.'
          : 'Campo desactivado correctamente.'
      )

    } catch (err) {
      setError(err.message)
    }
  }


  // ============================================================
  // REGLAS
  // ============================================================

  function openCreateRuleForm() {
    if (!ruleTypes.length) {
      setError(
        'No se encuentran disponibles los tipos de reglas. Recarga la pantalla o verifica el catálogo antes de crear una regla.'
      )
      return
    }

    const active = fields.filter((field) => field.estado)
    const firstField = active[0] || fields[0]
    const secondField = active[1] || active[0] || fields[1] || fields[0]
    const firstRuleType = ruleTypes[0]

    setEditingRule(null)
    setRuleForm({
      ...initialRuleForm,
      tipo_regla_id: firstRuleType?.tipo_regla_id
        ? String(firstRuleType.tipo_regla_id)
        : '',
      campo_principal_id: firstField?.campo_id
        ? String(firstField.campo_id)
        : '',
      campo_referencia_id: secondField?.campo_id
        ? String(secondField.campo_id)
        : '',
      campo_condicion_id: firstField?.campo_id
        ? String(firstField.campo_id)
        : '',
      accion_condicional: '',
    })
    setError('')
    setSuccess('')
    setRuleFormOpen(true)
    setFieldFormOpen(false)
  }


  function openEditRuleForm(rule) {
    const params = parameterMap(rule)

    const principal = rule.campos?.find(
      (item) => item.rol_campo === 'PRINCIPAL'
    )

    // Compatibilidad de lectura con reglas COMPARISON creadas antes de INC-04.
    const comparisonPrincipal =
      principal ||
      rule.campos?.find((item) => item.rol_campo === 'ORIGEN')

    const reference =
      rule.campos?.find((item) => item.rol_campo === 'REFERENCIA') ||
      rule.campos?.find((item) => item.rol_campo === 'DESTINO')

    const condition = rule.campos?.find(
      (item) => item.rol_campo === 'CONDICION'
    )

    const legacyValues = Array.isArray(params.valor)
      ? params.valor
      : params.valor
        ? [params.valor]
        : []

    setEditingRule(rule)
    setRuleForm({
      ...initialRuleForm,
      tipo_regla_id: String(rule.tipo_regla_id),
      nombre: rule.nombre || '',
      descripcion: rule.descripcion || '',
      campo_principal_id: principal?.campo_id
        ? String(principal.campo_id)
        : comparisonPrincipal?.campo_id
          ? String(comparisonPrincipal.campo_id)
          : '',
      campo_referencia_id: reference?.campo_id
        ? String(reference.campo_id)
        : '',
      campo_condicion_id: condition?.campo_id
        ? String(condition.campo_id)
        : '',
      comparacion_operador: params.operador || '=',
      condicion_operador:
        params.condicion_operador || params.operador || '=',
      condicion_valor:
        params.condicion_valor || legacyValues[0] || '',
      accion_condicional: params.accion || '',
      accion_valor: params.accion_valor || '',
      accion_valores: params.accion_valores || '',
      min: params.min || '',
      max: params.max || '',
      valores:
        params.valores || legacyValues.join('\n'),
      patron: params.patron || '',
      longitud_min: params.longitud_min || '',
      longitud_max: params.longitud_max || '',
    })

    setError('')
    setSuccess('')
    setRuleFormOpen(true)
    setFieldFormOpen(false)
  }


  function closeRuleForm() {
    setRuleFormOpen(false)
    setEditingRule(null)
    setRuleForm(initialRuleForm)
    setError('')
  }


  function handleRuleChange(event) {
    const { name, value } = event.target

    setRuleForm((current) => {
      const next = {
        ...current,
        [name]: value,
      }

      if (name === 'campo_condicion_id') {
        const field = fields.find(
          (item) => item.campo_id === Number(value)
        )
        const operators = operatorsForField(field)
        if (!operators.includes(next.condicion_operador)) {
          next.condicion_operador = operators[0]
        }
      }

      if (name === 'campo_principal_id') {
        const field = fields.find(
          (item) => item.campo_id === Number(value)
        )

        if (selectedRuleTypeCode() === 'COMPARISON') {
          const operators = operatorsForField(field)
          if (!operators.includes(next.comparacion_operador)) {
            next.comparacion_operador = operators[0]
          }
        }

        if (selectedRuleTypeCode() === 'CONDITIONAL') {
          const actions = conditionalActionsForField(field).map(
            (action) => action.value
          )
          if (next.accion_condicional && !actions.includes(next.accion_condicional)) {
            next.accion_condicional = ''
            next.accion_valor = ''
            next.accion_valores = ''
          }
        }
      }

      if (name === 'accion_condicional') {
        next.accion_valor = ''
        next.accion_valores = ''
      }

      return next
    })
  }


  function selectedRuleTypeCode() {
    return ruleTypes.find(
      (type) =>
        type.tipo_regla_id === Number(ruleForm.tipo_regla_id)
    )?.codigo || ''
  }


  function buildRulePayload() {
    const code = selectedRuleTypeCode()

    const payload = {
      tipo_regla_id: Number(ruleForm.tipo_regla_id),
      nombre: ruleForm.nombre.trim(),
      descripcion: ruleForm.descripcion.trim() || null,
      campos: [],
      parametros: [],
    }

    if (code === 'COMPARISON') {
      if (ruleForm.campo_principal_id === ruleForm.campo_referencia_id) {
        throw new Error(
          'La comparación requiere dos campos diferentes.'
        )
      }

      payload.campos = [
        {
          campo_id: Number(ruleForm.campo_principal_id),
          rol_campo: 'PRINCIPAL',
        },
        {
          campo_id: Number(ruleForm.campo_referencia_id),
          rol_campo: 'REFERENCIA',
        },
      ]

      payload.parametros = [
        {
          clave: 'operador',
          valor: ruleForm.comparacion_operador,
          orden: 1,
        },
      ]

      return payload
    }

    if (code === 'CONDITIONAL') {
      if (!ruleForm.campo_condicion_id || !ruleForm.campo_principal_id) {
        throw new Error(
          'Selecciona el campo condición y el campo objetivo.'
        )
      }

      if (ruleForm.campo_condicion_id === ruleForm.campo_principal_id) {
        throw new Error(
          'La condición y la consecuencia deben utilizar campos diferentes.'
        )
      }

      if (!ruleForm.accion_condicional) {
        throw new Error(
          'Selecciona la consecuencia que se aplicará cuando se cumpla la condición.'
        )
      }

      payload.campos = [
        {
          campo_id: Number(ruleForm.campo_condicion_id),
          rol_campo: 'CONDICION',
        },
        {
          campo_id: Number(ruleForm.campo_principal_id),
          rol_campo: 'PRINCIPAL',
        },
      ]

      const parameters = [
        {
          clave: 'condicion_operador',
          valor: ruleForm.condicion_operador,
          orden: 1,
        },
        {
          clave: 'condicion_valor',
          valor: ruleForm.condicion_valor.trim(),
          orden: 2,
        },
        {
          clave: 'accion',
          valor: ruleForm.accion_condicional,
          orden: 3,
        },
      ]

      if (ruleForm.accion_condicional === 'ALLOWED_VALUES') {
        const values = normalizeAllowedValues(ruleForm.accion_valores)
        if (!values.length) {
          throw new Error(
            'Ingresa al menos un valor permitido para la consecuencia.'
          )
        }
        parameters.push({
          clave: 'accion_valores',
          valor: values.join(','),
          orden: 4,
        })
      } else if (ruleForm.accion_condicional !== 'REQUIRED') {
        if (!ruleForm.accion_valor.trim()) {
          throw new Error(
            'Ingresa el valor esperado para la consecuencia.'
          )
        }
        parameters.push({
          clave: 'accion_valor',
          valor: ruleForm.accion_valor.trim(),
          orden: 4,
        })
      }

      payload.parametros = parameters
      return payload
    }

    payload.campos = [
      {
        campo_id: Number(ruleForm.campo_principal_id),
        rol_campo: 'PRINCIPAL',
      },
    ]

    if (code === 'REQUIRED') {
      return payload
    }

    if (code === 'RANGE') {
      payload.parametros = [
        {
          clave: 'min',
          valor: ruleForm.min.trim(),
          orden: 1,
        },
        {
          clave: 'max',
          valor: ruleForm.max.trim(),
          orden: 2,
        },
      ]
      return payload
    }

    if (code === 'ALLOWED_VALUES') {
      const values = normalizeAllowedValues(ruleForm.valores)
      if (!values.length) {
        throw new Error('Ingresa al menos un valor permitido.')
      }
      payload.parametros = [
        {
          clave: 'valores',
          valor: values.join(','),
          orden: 1,
        },
      ]
      return payload
    }

    if (code === 'FORMAT') {
      const parameters = []

      if (ruleForm.patron.trim()) {
        parameters.push({
          clave: 'patron',
          valor: ruleForm.patron.trim(),
          orden: parameters.length + 1,
        })
      }

      if (ruleForm.longitud_min !== '') {
        parameters.push({
          clave: 'longitud_min',
          valor: String(ruleForm.longitud_min),
          orden: parameters.length + 1,
        })
      }

      if (ruleForm.longitud_max !== '') {
        parameters.push({
          clave: 'longitud_max',
          valor: String(ruleForm.longitud_max),
          orden: parameters.length + 1,
        })
      }

      if (!parameters.length) {
        throw new Error(
          'Configura un patrón o una longitud para la regla FORMAT.'
        )
      }

      payload.parametros = parameters
      return payload
    }

    return payload
  }


  async function handleRuleSubmit(event) {
    event.preventDefault()

    if (!selectedModel) {
      return
    }

    setSavingRule(true)
    setError('')
    setSuccess('')

    try {
      const payload = buildRulePayload()

      if (editingRule) {
        const updated = await updateRule(
          editingRule.regla_id,
          payload,
        )

        setRules((current) =>
          current.map((rule) =>
            rule.regla_id === updated.regla_id
              ? updated
              : rule
          )
        )

        setSuccess('Regla modificada correctamente.')

      } else {
        const created = await createRule(
          selectedModel.modelo_id,
          payload,
        )

        setRules((current) => [
          ...current,
          created,
        ])

        setSuccess('Regla creada correctamente.')
      }

      setRuleFormOpen(false)
      setEditingRule(null)
      setRuleForm(initialRuleForm)

    } catch (err) {
      setError(err.message)

    } finally {
      setSavingRule(false)
    }
  }


  async function handleRuleStatus(rule) {
    const newStatus = !rule.estado
    const action = newStatus ? 'reactivar' : 'desactivar'

    const confirmed = window.confirm(
      `¿Deseas ${action} la regla "${rule.nombre}"?`
    )

    if (!confirmed) {
      return
    }

    setError('')
    setSuccess('')

    try {
      const updated = await changeRuleStatus(
        rule.regla_id,
        newStatus,
      )

      setRules((current) =>
        current.map((item) =>
          item.regla_id === updated.regla_id
            ? updated
            : item
        )
      )

      setSuccess(
        newStatus
          ? 'Regla reactivada correctamente.'
          : 'Regla desactivada correctamente.'
      )

    } catch (err) {
      setError(err.message)
    }
  }


  const activeFields = useMemo(
    () => fields.filter((field) => field.estado).length,
    [fields]
  )

  const activeRules = useMemo(
    () => rules.filter((rule) => rule.estado).length,
    [rules]
  )

  const ruleTypeCode = selectedRuleTypeCode()

  const comparisonPrincipalField = fields.find(
    (field) => field.campo_id === Number(ruleForm.campo_principal_id)
  )
  const conditionField = fields.find(
    (field) => field.campo_id === Number(ruleForm.campo_condicion_id)
  )
  const conditionalTargetField = fields.find(
    (field) => field.campo_id === Number(ruleForm.campo_principal_id)
  )

  const comparisonOperators = operatorsForField(comparisonPrincipalField)
  const conditionOperators = operatorsForField(conditionField)
  const conditionalActions = conditionalActionsForField(conditionalTargetField)

  const conditionalPreview = (() => {
    if (ruleTypeCode !== 'CONDITIONAL') {
      return ''
    }

    const conditionName = fieldDisplayName(conditionField) || '[campo condición]'
    const targetName = fieldDisplayName(conditionalTargetField) || '[campo objetivo]'
    const conditionValue = ruleForm.condicion_valor || '[valor]'

    if (!ruleForm.accion_condicional) {
      return `SI ${conditionName} ${ruleForm.condicion_operador} ${conditionValue} → ENTONCES ${targetName} [consecuencia]`
    }

    if (ruleForm.accion_condicional === 'REQUIRED') {
      return `SI ${conditionName} ${ruleForm.condicion_operador} ${conditionValue} → ENTONCES ${targetName} es obligatorio`
    }

    if (ruleForm.accion_condicional === 'ALLOWED_VALUES') {
      const values = normalizeAllowedValues(ruleForm.accion_valores).join(', ') || '[valores]'
      return `SI ${conditionName} ${ruleForm.condicion_operador} ${conditionValue} → ENTONCES ${targetName} pertenece a [${values}]`
    }

    const symbol = conditionalActionSymbol(ruleForm.accion_condicional)
    return `SI ${conditionName} ${ruleForm.condicion_operador} ${conditionValue} → ENTONCES ${targetName} ${symbol} ${ruleForm.accion_valor || '[valor]'}`
  })()


  if (loading) {
    return (
      <div className="configuration-loading">
        Cargando configuración...
      </div>
    )
  }


  return (
    <section className="configuration-page">

      <header className="configuration-header">
        <div>
          <span className="eyebrow">
            CONFIGURACIÓN
          </span>

          <h1>
            Configuración de campos y reglas
          </h1>

          <p>
            Define la estructura de cada modelo y las reglas de negocio
            utilizadas posteriormente para generar datos de prueba.
          </p>
        </div>
      </header>


      <section className="configuration-context-card">
        <div className="configuration-context-copy">
          <span className="eyebrow">
            Contexto de trabajo
          </span>

          <h2>
            Selecciona proyecto y modelo
          </h2>

          <p>
            Los campos y reglas se configuran sobre un modelo de datos específico.
          </p>
        </div>

        <div className="configuration-selectors">
          <label>
            Proyecto
            <select
              value={selectedProject?.proyecto_id || ''}
              onChange={handleProjectSelection}
              disabled={!projects.length}
            >
              {!projects.length && (
                <option value="">
                  Sin proyectos disponibles
                </option>
              )}

              {projects.map((project) => (
                <option
                  key={project.proyecto_id}
                  value={project.proyecto_id}
                >
                  {project.nombre}
                  {!project.estado ? ' · Inactivo' : ''}
                </option>
              ))}
            </select>
          </label>

          <label>
            Modelo
            <select
              value={selectedModel?.modelo_id || ''}
              onChange={handleModelSelection}
              disabled={loadingModels || !models.length}
            >
              {!models.length && (
                <option value="">
                  {loadingModels
                    ? 'Cargando modelos...'
                    : 'Sin modelos disponibles'}
                </option>
              )}

              {models.map((model) => (
                <option
                  key={model.modelo_id}
                  value={model.modelo_id}
                >
                  {model.nombre}
                  {!model.estado ? ' · Inactivo' : ''}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>


      {selectedModel && (
        <section className="configuration-summary">
          <article className="configuration-summary-card fields">
            <span>Campos</span>
            <strong>{fields.length}</strong>
            <small>{activeFields} activos</small>
          </article>

          <article className="configuration-summary-card rules">
            <span>Reglas</span>
            <strong>{rules.length}</strong>
            <small>{activeRules} activas</small>
          </article>

          <article className="configuration-summary-card model">
            <span>Modelo</span>
            <strong className="configuration-summary-name">
              {selectedModel.nombre}
            </strong>
            <small>
              {selectedModel.estado ? 'Activo' : 'Inactivo'}
            </small>
          </article>

          <article className="configuration-summary-card project">
            <span>Proyecto</span>
            <strong className="configuration-summary-name">
              {selectedProject?.nombre}
            </strong>
            <small>
              {selectedProject?.estado ? 'Activo' : 'Inactivo'}
            </small>
          </article>
        </section>
      )}


      {error && (
        <div className="projects-message error">
          {error}
        </div>
      )}

      {success && (
        <div className="projects-message success">
          {success}
        </div>
      )}

      {catalogWarning && (
        <div className="configuration-catalog-warning">
          {catalogWarning}
        </div>
      )}


      {selectedModel && !configurationEnabled && (
        <div className="project-inactive-notice">
          La configuración se encuentra en modo consulta porque el proyecto
          o el modelo seleccionado está inactivo.
        </div>
      )}


      {fieldFormOpen && (
        <section
          ref={fieldFormRef}
          className="configuration-form-card configuration-scroll-target"
        >
          <div className="project-form-header">
            <div>
              <span className="eyebrow">
                {editingField
                  ? 'Modificar registro'
                  : 'Nuevo registro'}
              </span>

              <h2>
                {editingField
                  ? 'Modificar campo'
                  : 'Crear campo'}
              </h2>
            </div>

            <button
              type="button"
              className="form-close-button"
              onClick={closeFieldForm}
            >
              ×
            </button>
          </div>

          <form
            className="configuration-form"
            onSubmit={handleFieldSubmit}
          >
            <label>
              Nombre del campo
              <input
                name="nombre"
                value={fieldForm.nombre}
                onChange={handleFieldChange}
                minLength="2"
                maxLength="100"
                required
                placeholder="Ej.: edad_cliente"
              />
            </label>

            <label>
              Tipo de dato
              <select
                name="tipo_dato_id"
                value={fieldForm.tipo_dato_id}
                onChange={handleFieldChange}
                required
              >
                <option value="">
                  Selecciona tipo
                </option>

                {dataTypes
                  .filter((type) => type.estado)
                  .map((type) => (
                    <option
                      key={type.tipo_dato_id}
                      value={type.tipo_dato_id}
                    >
                      {type.nombre} ({type.codigo})
                    </option>
                  ))}
              </select>
            </label>

            <label>
              Orden
              <input
                type="number"
                name="orden"
                value={fieldForm.orden}
                onChange={handleFieldChange}
                min="1"
                required
              />
            </label>

            <label className="configuration-form-wide">
              Descripción
              <textarea
                name="descripcion"
                value={fieldForm.descripcion}
                onChange={handleFieldChange}
                maxLength="250"
                rows="3"
                placeholder="Describe el uso del campo dentro del modelo"
              />
            </label>

            <div className="configuration-form-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={closeFieldForm}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={savingField}
              >
                {savingField
                  ? 'Guardando...'
                  : editingField
                    ? 'Guardar cambios'
                    : 'Crear campo'}
              </button>
            </div>
          </form>
        </section>
      )}


      {ruleFormOpen && (
        <section
          ref={ruleFormRef}
          className="configuration-form-card rule-form-card configuration-scroll-target"
        >
          <div className="project-form-header">
            <div>
              <span className="eyebrow">
                {editingRule
                  ? 'Modificar configuración'
                  : 'Nueva configuración'}
              </span>

              <h2>
                {editingRule
                  ? 'Modificar regla'
                  : 'Crear regla de negocio'}
              </h2>
            </div>

            <button
              type="button"
              className="form-close-button"
              onClick={closeRuleForm}
            >
              ×
            </button>
          </div>

          <form
            className="configuration-form"
            onSubmit={handleRuleSubmit}
          >
            <label>
              Nombre de la regla
              <input
                name="nombre"
                value={ruleForm.nombre}
                onChange={handleRuleChange}
                minLength="2"
                maxLength="150"
                required
                placeholder="Ej.: Rango edad cliente"
              />
            </label>

            <label>
              Tipo de regla
              <select
                name="tipo_regla_id"
                value={ruleForm.tipo_regla_id}
                onChange={handleRuleChange}
                required
              >
                <option value="">
                  Selecciona tipo
                </option>

                {ruleTypes
                  .filter((type) => type.estado)
                  .map((type) => (
                    <option
                      key={type.tipo_regla_id}
                      value={type.tipo_regla_id}
                    >
                      {type.nombre} ({type.codigo})
                    </option>
                  ))}
              </select>
            </label>

            <label className="configuration-form-wide">
              Descripción
              <textarea
                name="descripcion"
                value={ruleForm.descripcion}
                onChange={handleRuleChange}
                rows="3"
                placeholder="Describe la condición que debe cumplir la regla"
              />
            </label>


            {ruleTypeCode === 'COMPARISON' ? (
              <>
                <label>
                  Campo principal
                  <select
                    name="campo_principal_id"
                    value={ruleForm.campo_principal_id}
                    onChange={handleRuleChange}
                    required
                  >
                    <option value="">Selecciona campo</option>
                    {fields
                      .filter((field) => field.estado)
                      .map((field) => (
                        <option key={field.campo_id} value={field.campo_id}>
                          {fieldDisplayName(field)} · {field.tipo_dato_codigo}
                        </option>
                      ))}
                  </select>
                </label>

                <label>
                  Operador
                  <select
                    name="comparacion_operador"
                    value={ruleForm.comparacion_operador}
                    onChange={handleRuleChange}
                    required
                  >
                    {comparisonOperators.map((operator) => (
                      <option key={operator} value={operator}>
                        {operator}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Campo de referencia
                  <select
                    name="campo_referencia_id"
                    value={ruleForm.campo_referencia_id}
                    onChange={handleRuleChange}
                    required
                  >
                    <option value="">Selecciona campo</option>
                    {fields
                      .filter((field) =>
                        field.estado &&
                        field.campo_id !== Number(ruleForm.campo_principal_id) &&
                        (
                          !comparisonPrincipalField ||
                          field.tipo_dato_codigo === comparisonPrincipalField.tipo_dato_codigo ||
                          (
                            ['INTEGER', 'DECIMAL'].includes(field.tipo_dato_codigo) &&
                            ['INTEGER', 'DECIMAL'].includes(comparisonPrincipalField.tipo_dato_codigo)
                          )
                        )
                      )
                      .map((field) => (
                        <option key={field.campo_id} value={field.campo_id}>
                          {fieldDisplayName(field)} · {field.tipo_dato_codigo}
                        </option>
                      ))}
                  </select>
                </label>

                <div className="rule-help configuration-form-wide">
                  La comparación se interpreta como: <strong>Campo principal operador Campo de referencia</strong>.
                </div>
              </>
            ) : ruleTypeCode === 'CONDITIONAL' ? (
              <>
                <div className="conditional-section configuration-form-wide">
                  <span className="conditional-section-title">SI · Condición</span>
                  <p>Define cuándo debe activarse la consecuencia.</p>
                </div>

                <label>
                  Campo condición
                  <select
                    name="campo_condicion_id"
                    value={ruleForm.campo_condicion_id}
                    onChange={handleRuleChange}
                    required
                  >
                    <option value="">Selecciona campo</option>
                    {fields
                      .filter((field) => field.estado)
                      .map((field) => (
                        <option key={field.campo_id} value={field.campo_id}>
                          {fieldDisplayName(field)} · {field.tipo_dato_codigo}
                        </option>
                      ))}
                  </select>
                </label>

                <label>
                  Operador de condición
                  <select
                    name="condicion_operador"
                    value={ruleForm.condicion_operador}
                    onChange={handleRuleChange}
                    required
                  >
                    {conditionOperators.map((operator) => (
                      <option key={operator} value={operator}>
                        {operator}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Valor de condición
                  <input
                    name="condicion_valor"
                    value={ruleForm.condicion_valor}
                    onChange={handleRuleChange}
                    required
                    placeholder="Ej.: VIP"
                  />
                </label>

                <div className="conditional-section consequence configuration-form-wide">
                  <span className="conditional-section-title">ENTONCES · Consecuencia</span>
                  <p>Define qué debe cumplir otro campo cuando la condición sea verdadera.</p>
                </div>

                <label>
                  Campo objetivo
                  <select
                    name="campo_principal_id"
                    value={ruleForm.campo_principal_id}
                    onChange={handleRuleChange}
                    required
                  >
                    <option value="">Selecciona campo</option>
                    {fields
                      .filter((field) =>
                        field.estado &&
                        field.campo_id !== Number(ruleForm.campo_condicion_id)
                      )
                      .map((field) => (
                        <option key={field.campo_id} value={field.campo_id}>
                          {fieldDisplayName(field)} · {field.tipo_dato_codigo}
                        </option>
                      ))}
                  </select>
                </label>

                <label>
                  Consecuencia
                  <select
                    name="accion_condicional"
                    value={ruleForm.accion_condicional}
                    onChange={handleRuleChange}
                    required
                  >
                    <option value="">Selecciona consecuencia</option>
                    {conditionalActions.map((action) => (
                      <option key={action.value} value={action.value}>
                        {action.label}
                      </option>
                    ))}
                  </select>
                </label>

                {ruleForm.accion_condicional === 'ALLOWED_VALUES' ? (
                  <label className="configuration-form-wide">
                    Valores permitidos para la consecuencia
                    <textarea
                      name="accion_valores"
                      value={ruleForm.accion_valores}
                      onChange={handleRuleChange}
                      rows="3"
                      required
                      placeholder={'CLP\nUSD\nEUR'}
                    />
                    <small>Ingresa un valor por línea o sepáralos por coma.</small>
                  </label>
                ) : ruleForm.accion_condicional && ruleForm.accion_condicional !== 'REQUIRED' ? (
                  <label>
                    Valor esperado
                    <input
                      name="accion_valor"
                      value={ruleForm.accion_valor}
                      onChange={handleRuleChange}
                      required
                      placeholder="Ej.: 15"
                    />
                  </label>
                ) : null}

                <div className="conditional-preview configuration-form-wide">
                  <span>Lectura de la regla</span>
                  <strong>{conditionalPreview}</strong>
                </div>
              </>
            ) : (
              <label>
                Campo asociado
                <select
                  name="campo_principal_id"
                  value={ruleForm.campo_principal_id}
                  onChange={handleRuleChange}
                  required
                >
                  <option value="">Selecciona campo</option>
                  {fields
                    .filter((field) => field.estado)
                    .map((field) => (
                      <option key={field.campo_id} value={field.campo_id}>
                        {fieldDisplayName(field)} · {field.tipo_dato_codigo}
                      </option>
                    ))}
                </select>
              </label>
            )}


            {ruleTypeCode === 'RANGE' && (
              <>
                <label>
                  Valor mínimo
                  <input
                    name="min"
                    value={ruleForm.min}
                    onChange={handleRuleChange}
                    required
                    placeholder="Ej.: 18"
                  />
                </label>

                <label>
                  Valor máximo
                  <input
                    name="max"
                    value={ruleForm.max}
                    onChange={handleRuleChange}
                    required
                    placeholder="Ej.: 65"
                  />
                </label>
              </>
            )}


            {ruleTypeCode === 'ALLOWED_VALUES' && (
              <label className="configuration-form-wide">
                Valores permitidos
                <textarea
                  name="valores"
                  value={ruleForm.valores}
                  onChange={handleRuleChange}
                  rows="4"
                  required
                  placeholder={'PERSONA\nEMPRESA\nVIP'}
                />
                <small>
                  Ingresa un valor por línea o sepáralos por coma.
                </small>
              </label>
            )}


            {ruleTypeCode === 'FORMAT' && (
              <>
                <label>
                  Patrón
                  <input
                    name="patron"
                    value={ruleForm.patron}
                    onChange={handleRuleChange}
                    placeholder="Opcional"
                  />
                </label>

                <label>
                  Longitud mínima
                  <input
                    type="number"
                    min="0"
                    name="longitud_min"
                    value={ruleForm.longitud_min}
                    onChange={handleRuleChange}
                    placeholder="Ej.: 5"
                  />
                </label>

                <label>
                  Longitud máxima
                  <input
                    type="number"
                    min="0"
                    name="longitud_max"
                    value={ruleForm.longitud_max}
                    onChange={handleRuleChange}
                    placeholder="Ej.: 150"
                  />
                </label>
              </>
            )}




            {ruleTypeCode === 'REQUIRED' && (
              <div className="rule-help configuration-form-wide">
                Esta regla valida que el campo seleccionado tenga un valor informado.
                No requiere parámetros adicionales.
              </div>
            )}


            <div className="configuration-form-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={closeRuleForm}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={savingRule}
              >
                {savingRule
                  ? 'Guardando...'
                  : editingRule
                    ? 'Guardar cambios'
                    : 'Crear regla'}
              </button>
            </div>
          </form>
        </section>
      )}


      {!selectedProject ? (
        <section className="configuration-empty-state">
          No existen proyectos disponibles para configurar.
        </section>

      ) : !selectedModel ? (
        <section className="configuration-empty-state">
          El proyecto seleccionado no tiene modelos asociados.
          Crea primero un modelo desde M01.
        </section>

      ) : loadingConfiguration ? (
        <div className="configuration-loading">
          Cargando campos y reglas...
        </div>

      ) : (
        <>
          <section className="configuration-table-card">
            <div className="configuration-table-heading">
              <div>
                <span className="eyebrow">
                  Estructura del modelo
                </span>

                <h2>
                  Campos
                </h2>

                <p>
                  Define nombre, tipo de dato, orden y estado lógico de cada campo.
                </p>
              </div>

              <div className="configuration-heading-actions">
                <span className="projects-count">
                  {fields.length} registros
                </span>

                <button
                  type="button"
                  className="primary-button"
                  onClick={openCreateFieldForm}
                  disabled={!configurationEnabled}
                >
                  + Nuevo campo
                </button>
              </div>
            </div>

            <div className="table-responsive">
              <table className="configuration-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Campo</th>
                    <th>Tipo</th>
                    <th>Orden</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>

                <tbody>
                  {fields.length === 0 ? (
                    <tr>
                      <td
                        colSpan="6"
                        className="projects-empty"
                      >
                        El modelo aún no tiene campos configurados.
                      </td>
                    </tr>
                  ) : (
                    fields.map((field) => (
                      <tr key={field.campo_id}>
                        <td className="project-id">
                          {field.campo_id}
                        </td>

                        <td>
                          <div className="configuration-name-cell">
                            <strong>{field.nombre}</strong>
                            <small>
                              {field.descripcion || 'Sin descripción'}
                            </small>
                          </div>
                        </td>

                        <td>
                          <span className="data-type-pill">
                            {field.tipo_dato_codigo}
                          </span>
                        </td>

                        <td>{field.orden ?? '—'}</td>

                        <td>
                          <span
                            className={
                              field.estado
                                ? 'table-status active'
                                : 'table-status inactive'
                            }
                          >
                            {field.estado ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>

                        <td>
                          <div className="table-actions project-actions">
                            <button
                              type="button"
                              className="table-button edit"
                              onClick={() => openEditFieldForm(field)}
                              disabled={!configurationEnabled}
                            >
                              Editar
                            </button>

                            <button
                              type="button"
                              className={
                                field.estado
                                  ? 'table-button deactivate'
                                  : 'table-button activate'
                              }
                              onClick={() => handleFieldStatus(field)}
                              disabled={!selectedProject?.estado || !selectedModel?.estado}
                            >
                              {field.estado
                                ? 'Desactivar'
                                : 'Reactivar'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>


          <section className="configuration-table-card">
            <div className="configuration-table-heading">
              <div>
                <span className="eyebrow">
                  Reglas de negocio
                </span>

                <h2>
                  Reglas configuradas
                </h2>

                <p>
                  Asocia reglas a los campos y configura sus parámetros de validación.
                </p>
              </div>

              <div className="configuration-heading-actions">
                <span className="projects-count rules-count">
                  {rules.length} registros
                </span>

                <button
                  type="button"
                  className="primary-button"
                  onClick={openCreateRuleForm}
                  disabled={!configurationEnabled || fields.length === 0}
                >
                  + Nueva regla
                </button>
              </div>
            </div>

            {fields.length === 0 && (
              <div className="configuration-table-notice">
                Debes crear al menos un campo antes de configurar reglas.
              </div>
            )}

            <div className="table-responsive">
              <table className="configuration-table rules-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Regla</th>
                    <th>Tipo</th>
                    <th>Campo(s)</th>
                    <th>Parámetros</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>

                <tbody>
                  {rules.length === 0 ? (
                    <tr>
                      <td
                        colSpan="7"
                        className="projects-empty"
                      >
                        El modelo aún no tiene reglas configuradas.
                      </td>
                    </tr>
                  ) : (
                    rules.map((rule) => (
                      <tr key={rule.regla_id}>
                        <td className="project-id">
                          {rule.regla_id}
                        </td>

                        <td>
                          <div className="configuration-name-cell">
                            <strong>{rule.nombre}</strong>
                            <small>
                              {rule.descripcion || 'Sin descripción'}
                            </small>
                          </div>
                        </td>

                        <td>
                          <span className="rule-type-pill">
                            {rule.tipo_regla_codigo}
                          </span>
                        </td>

                        <td>
                          <div className="configuration-tags">
                            {(rule.campos || []).map((field) => (
                              <span
                                key={`${rule.regla_id}-${field.campo_id}-${field.rol_campo}`}
                                className="field-tag"
                              >
                                {fieldDisplayName(field)}
                                <small>{field.rol_campo}</small>
                              </span>
                            ))}
                          </div>
                        </td>

                        <td>
                          {ruleBusinessSummary(rule) ? (
                            <div className="configuration-parameters business-summary">
                              {ruleBusinessSummary(rule).map((line, index) => (
                                <span key={`${rule.regla_id}-summary-${index}`}>
                                  {line}
                                </span>
                              ))}
                            </div>
                          ) : (rule.parametros || []).length ? (
                            <div className="configuration-parameters">
                              {rule.parametros.map((parameter) => (
                                <span key={parameter.parametro_id}>
                                  <strong>{parameter.clave}</strong>
                                  {' = '}
                                  {parameter.valor}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="configuration-no-parameters">
                              Sin parámetros
                            </span>
                          )}
                        </td>

                        <td>
                          <span
                            className={
                              rule.estado
                                ? 'table-status active'
                                : 'table-status inactive'
                            }
                          >
                            {rule.estado ? 'Activa' : 'Inactiva'}
                          </span>
                        </td>

                        <td>
                          <div className="table-actions project-actions">
                            <button
                              type="button"
                              className="table-button edit"
                              onClick={() => openEditRuleForm(rule)}
                              disabled={!configurationEnabled}
                            >
                              Editar
                            </button>

                            <button
                              type="button"
                              className={
                                rule.estado
                                  ? 'table-button deactivate'
                                  : 'table-button activate'
                              }
                              onClick={() => handleRuleStatus(rule)}
                              disabled={!selectedProject?.estado || !selectedModel?.estado}
                            >
                              {rule.estado
                                ? 'Desactivar'
                                : 'Reactivar'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

    </section>
  )
}
