import { useFeedback } from '../components/FeedbackProvider'
import { useEffect, useMemo, useState } from 'react'

import {
  getProjects,
  createProject,
  updateProject,
  changeProjectStatus,
  getProjectModels,
  createModel,
  updateModel,
  changeModelStatus,
} from '../api/projects'


/*
2026-11-16
Se implementa la interfaz frontend del módulo M01
para la gestión de proyectos y modelos.

Permite:
- Consultar proyectos.
- Crear proyectos.
- Modificar proyectos.
- Activar o desactivar proyectos.
- Consultar modelos asociados.
- Crear modelos asociados a un proyecto.
- Modificar modelos.
- Activar o desactivar modelos.
*/


const initialProjectForm = {
  nombre: '',
  descripcion: '',
}


const initialModelForm = {
  nombre: '',
  descripcion: '',
}


export default function ProjectsPage() {

  // ============================================================
  // ESTADOS GENERALES
  // ============================================================

  const [projects, setProjects] = useState([])
  const [models, setModels] = useState([])

  const [loading, setLoading] = useState(true)
  const [loadingModels, setLoadingModels] = useState(false)

  const [savingProject, setSavingProject] = useState(false)
  const [savingModel, setSavingModel] = useState(false)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')


  const { confirmAction, notifySuccess } = useFeedback()


  // ============================================================
  // PROYECTO SELECCIONADO
  // ============================================================

  const [selectedProject, setSelectedProject] = useState(null)


  // ============================================================
  // FORMULARIO PROYECTO
  // ============================================================

  const [projectFormOpen, setProjectFormOpen] =
    useState(false)

  const [editingProject, setEditingProject] =
    useState(null)

  const [projectForm, setProjectForm] =
    useState(initialProjectForm)


  // ============================================================
  // FORMULARIO MODELO
  // ============================================================

  const [modelFormOpen, setModelFormOpen] =
    useState(false)

  const [editingModel, setEditingModel] =
    useState(null)

  const [modelForm, setModelForm] =
    useState(initialModelForm)


  // ============================================================
  // CARGA INICIAL
  // ============================================================

  useEffect(() => {
    loadProjects()
  }, [])


  async function loadProjects() {
    setLoading(true)
    setError('')

    try {
      const data = await getProjects()

      setProjects(data)

    } catch (err) {
      setError(err.message)

    } finally {
      setLoading(false)
    }
  }


  // ============================================================
  // CARGAR MODELOS
  // ============================================================

  async function loadModels(project) {

    setSelectedProject(project)

    setLoadingModels(true)

    setError('')
    setSuccess('')

    setModelFormOpen(false)
    setEditingModel(null)

    try {

      const data =
        await getProjectModels(project.proyecto_id)

      setModels(data)

    } catch (err) {

      setModels([])
      setError(err.message)

    } finally {

      setLoadingModels(false)
    }
  }


  // ============================================================
  // FORMULARIO PROYECTO
  // ============================================================

  function openCreateProjectForm() {

    setEditingProject(null)

    setProjectForm(initialProjectForm)

    setError('')
    setSuccess('')

    setProjectFormOpen(true)
  }


  function openEditProjectForm(project) {

    setEditingProject(project)

    setProjectForm({
      nombre: project.nombre || '',
      descripcion: project.descripcion || '',
    })

    setError('')
    setSuccess('')

    setProjectFormOpen(true)
  }


  function closeProjectForm() {

    setProjectFormOpen(false)

    setEditingProject(null)

    setProjectForm(initialProjectForm)

    setError('')
  }


  function handleProjectChange(event) {

    const { name, value } = event.target

    setProjectForm((current) => ({
      ...current,
      [name]: value,
    }))
  }


  async function handleProjectSubmit(event) {

    event.preventDefault()

    const accepted = await confirmAction({
      title: editingProject
        ? `¿Guardar los cambios del proyecto «${projectForm.nombre}»?`
        : `¿Crear el proyecto «${projectForm.nombre}»?`,
      description: 'Los cambios se guardarán en TestData Studio.',
      confirmText: editingProject ? 'Guardar cambios' : 'Crear proyecto',
      cancelText: 'Volver al formulario',
      summary: [{ label: 'Proyecto', value: projectForm.nombre }],
    })
    if (!accepted) return

    setSavingProject(true)

    setError('')
    setSuccess('')

    try {

      const payload = {
        nombre: projectForm.nombre.trim(),
        descripcion:
          projectForm.descripcion.trim() || null,
      }


      // --------------------------------------------------------
      // MODIFICAR
      // --------------------------------------------------------

      if (editingProject) {

        const updated =
          await updateProject(
            editingProject.proyecto_id,
            payload,
          )


        setProjects((current) =>
          current.map((project) =>
            project.proyecto_id ===
            updated.proyecto_id
              ? {
                  ...project,
                  ...updated,
                }
              : project
          )
        )


        if (
          selectedProject?.proyecto_id ===
          updated.proyecto_id
        ) {
          setSelectedProject((current) => ({
            ...current,
            ...updated,
          }))
        }


        notifySuccess(
          'Proyecto modificado correctamente.'
        )

      } else {

        // ------------------------------------------------------
        // CREAR
        // ------------------------------------------------------

        const created =
          await createProject(payload)


        setProjects((current) => [
          ...current,
          created,
        ])


        notifySuccess(
          'Proyecto creado correctamente.'
        )
      }


      setProjectFormOpen(false)

      setEditingProject(null)

      setProjectForm(initialProjectForm)


    } catch (err) {

      setError(err.message)

    } finally {

      setSavingProject(false)
    }
  }


  // ============================================================
  // CAMBIAR ESTADO PROYECTO
  // ============================================================

  async function handleProjectStatus(project) {

    const newStatus = !project.estado

    const action =
      newStatus
        ? 'reactivar'
        : 'desactivar'


    const confirmed = await confirmAction({
      title: `¿Deseas ${action} el proyecto «${project.nombre}»?`,
      description: 'Este cambio de estado afectará su disponibilidad para los usuarios.',
      confirmText: newStatus ? 'Reactivar proyecto' : 'Desactivar proyecto',
      summary: [{ label: 'Proyecto', value: project.nombre }, { label: 'Nuevo estado', value: newStatus ? 'Activo' : 'Inactivo' }],
    })


    if (!confirmed) {
      return
    }


    setError('')
    setSuccess('')


    try {

      const updated =
        await changeProjectStatus(
          project.proyecto_id,
          newStatus,
        )


      setProjects((current) =>
        current.map((item) =>
          item.proyecto_id ===
          updated.proyecto_id
            ? {
                ...item,
                ...updated,
              }
            : item
        )
      )


      if (
        selectedProject?.proyecto_id ===
        updated.proyecto_id
      ) {

        setSelectedProject((current) => ({
          ...current,
          ...updated,
        }))
      }


      notifySuccess(
        newStatus
          ? 'Proyecto reactivado correctamente.'
          : 'Proyecto desactivado correctamente.'
      )


    } catch (err) {

      setError(err.message)
    }
  }


  // ============================================================
  // FORMULARIO MODELO
  // ============================================================

  function openCreateModelForm() {

    if (!selectedProject) {
      return
    }


    setEditingModel(null)

    setModelForm(initialModelForm)

    setError('')
    setSuccess('')

    setModelFormOpen(true)
  }


  function openEditModelForm(model) {

    setEditingModel(model)

    setModelForm({
      nombre: model.nombre || '',
      descripcion: model.descripcion || '',
    })

    setError('')
    setSuccess('')

    setModelFormOpen(true)
  }


  function closeModelForm() {

    setModelFormOpen(false)

    setEditingModel(null)

    setModelForm(initialModelForm)

    setError('')
  }


  function handleModelChange(event) {

    const { name, value } = event.target

    setModelForm((current) => ({
      ...current,
      [name]: value,
    }))
  }


  async function handleModelSubmit(event) {

    event.preventDefault()


    if (!selectedProject) {
      return
    }


    const accepted = await confirmAction({
      title: editingModel
        ? `¿Guardar los cambios del modelo «${modelForm.nombre}»?`
        : `¿Crear el modelo «${modelForm.nombre}»?`,
      description: 'El modelo quedará asociado al proyecto seleccionado.',
      confirmText: editingModel ? 'Guardar cambios' : 'Crear modelo',
      cancelText: 'Volver al formulario',
      summary: [{ label: 'Modelo', value: modelForm.nombre }, { label: 'Proyecto', value: selectedProject?.nombre || '—' }],
    })
    if (!accepted) return

    setSavingModel(true)

    setError('')
    setSuccess('')


    try {

      const payload = {
        nombre: modelForm.nombre.trim(),
        descripcion:
          modelForm.descripcion.trim() || null,
      }


      // --------------------------------------------------------
      // MODIFICAR MODELO
      // --------------------------------------------------------

      if (editingModel) {

        const updated =
          await updateModel(
            editingModel.modelo_id,
            payload,
          )


        setModels((current) =>
          current.map((model) =>
            model.modelo_id ===
            updated.modelo_id
              ? updated
              : model
          )
        )


        notifySuccess(
          'Modelo modificado correctamente.'
        )

      } else {

        // ------------------------------------------------------
        // CREAR MODELO
        // ------------------------------------------------------

        const created =
          await createModel(
            selectedProject.proyecto_id,
            payload,
          )


        setModels((current) => [
          ...current,
          created,
        ])


        // Actualiza visualmente cantidad de modelos
        setProjects((current) =>
          current.map((project) =>
            project.proyecto_id ===
            selectedProject.proyecto_id
              ? {
                  ...project,
                  cantidad_modelos:
                    Number(
                      project.cantidad_modelos || 0
                    ) + 1,
                }
              : project
          )
        )


        setSelectedProject((current) => ({
          ...current,
          cantidad_modelos:
            Number(
              current?.cantidad_modelos || 0
            ) + 1,
        }))


        notifySuccess(
          'Modelo asociado correctamente al proyecto.'
        )
      }


      setModelFormOpen(false)

      setEditingModel(null)

      setModelForm(initialModelForm)


    } catch (err) {

      setError(err.message)

    } finally {

      setSavingModel(false)
    }
  }


  // ============================================================
  // CAMBIAR ESTADO MODELO
  // ============================================================

  async function handleModelStatus(model) {

    const newStatus = !model.estado

    const action =
      newStatus
        ? 'reactivar'
        : 'desactivar'


    const confirmed = await confirmAction({
      title: `¿Deseas ${action} el modelo «${model.nombre}»?`,
      description: 'Este cambio actualizará su disponibilidad en la plataforma.',
      confirmText: newStatus ? 'Reactivar modelo' : 'Desactivar modelo',
      summary: [{ label: 'Modelo', value: model.nombre }, { label: 'Nuevo estado', value: newStatus ? 'Activo' : 'Inactivo' }],
    })


    if (!confirmed) {
      return
    }


    setError('')
    setSuccess('')


    try {

      const updated =
        await changeModelStatus(
          model.modelo_id,
          newStatus,
        )


      setModels((current) =>
        current.map((item) =>
          item.modelo_id ===
          updated.modelo_id
            ? updated
            : item
        )
      )


      notifySuccess(
        newStatus
          ? 'Modelo reactivado correctamente.'
          : 'Modelo desactivado correctamente.'
      )


    } catch (err) {

      setError(err.message)
    }
  }


  // ============================================================
  // RESUMEN
  // ============================================================

  const activeProjects = useMemo(
    () =>
      projects.filter(
        (project) => project.estado
      ).length,
    [projects]
  )


  const totalModels = useMemo(
    () =>
      projects.reduce(
        (total, project) =>
          total +
          Number(project.cantidad_modelos || 0),
        0
      ),
    [projects]
  )


  // ============================================================
  // CARGANDO
  // ============================================================

  if (loading) {

    return (
      <div className="projects-loading">
        Cargando proyectos...
      </div>
    )
  }


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <section className="projects-page">


      {/* ======================================================
          CABECERA
          ====================================================== */}

      <header className="projects-header">

        <div>

          <span className="eyebrow">
            M01 · Proyectos y modelos
          </span>

          <h1>
            Gestión de proyectos y modelos
          </h1>

          <p>
            Administra los proyectos de prueba y los
            modelos de datos asociados a cada proyecto.
          </p>

        </div>


        <button
          type="button"
          className="primary-button projects-new-button"
          onClick={openCreateProjectForm}
        >
          + Nuevo proyecto
        </button>

      </header>


      {/* ======================================================
          RESUMEN
          ====================================================== */}

      <section className="projects-summary">

        <article className="projects-summary-card">

          <span>
            Total proyectos
          </span>

          <strong>
            {projects.length}
          </strong>

        </article>


        <article className="projects-summary-card active">

          <span>
            Activos
          </span>

          <strong>
            {activeProjects}
          </strong>

        </article>


        <article className="projects-summary-card inactive">

          <span>
            Inactivos
          </span>

          <strong>
            {projects.length - activeProjects}
          </strong>

        </article>


        <article className="projects-summary-card models">

          <span>
            Modelos
          </span>

          <strong>
            {totalModels}
          </strong>

        </article>

      </section>


      {/* ======================================================
          MENSAJES
          ====================================================== */}

      {error && (

        <div className="projects-message error">
          {error}
        </div>

      )}



{/* ======================================================
          FORMULARIO PROYECTO
          ====================================================== */}

      {projectFormOpen && (

        <section className="project-form-card">

          <div className="project-form-header">

            <div>

              <span className="eyebrow">

                {editingProject
                  ? 'Modificar registro'
                  : 'Nuevo registro'}

              </span>


              <h2>

                {editingProject
                  ? 'Modificar proyecto'
                  : 'Crear proyecto'}

              </h2>

            </div>


            <button
              type="button"
              className="form-close-button"
              onClick={closeProjectForm}
            >
              ×
            </button>

          </div>


          <form
            className="project-form"
            onSubmit={handleProjectSubmit}
          >

            <label>

              Nombre del proyecto

              <input
                name="nombre"
                value={projectForm.nombre}
                onChange={handleProjectChange}
                minLength="2"
                maxLength="150"
                required
                placeholder="Ej.: Proyecto clientes QA"
              />

            </label>


            <label>

              Descripción

              <textarea
                name="descripcion"
                value={projectForm.descripcion}
                onChange={handleProjectChange}
                maxLength="500"
                rows="4"
                placeholder="Describe brevemente el objetivo del proyecto"
              />

            </label>


            <div className="form-actions">

              <button
                type="button"
                className="secondary-button"
                onClick={closeProjectForm}
              >
                Cancelar
              </button>


              <button
                type="submit"
                className="primary-button"
                disabled={savingProject}
              >

                {savingProject
                  ? 'Guardando...'
                  : editingProject
                    ? 'Guardar cambios'
                    : 'Crear proyecto'}

              </button>

            </div>

          </form>

        </section>

      )}


      {/* ======================================================
          TABLA PROYECTOS
          ====================================================== */}

      <section className="projects-table-card">

        <div className="projects-table-heading">

          <div>

            <h2>
              Proyectos registrados
            </h2>

            <p>
              Proyectos disponibles para el
              Analista/Tester autenticado.
            </p>

          </div>


          <span className="projects-count">
            {projects.length} registros
          </span>

        </div>


        <div className="table-responsive">

          <table className="projects-table">

            <thead>

              <tr>
                <th>ID</th>
                <th>Proyecto</th>
                <th>Modelos</th>
                <th>Estado</th>
                <th>Fecha creación</th>
                <th>Acciones</th>
              </tr>

            </thead>


            <tbody>

              {projects.length === 0 ? (

                <tr>

                  <td
                    colSpan="6"
                    className="projects-empty"
                  >
                    No existen proyectos registrados.
                  </td>

                </tr>

              ) : (

                projects.map((project) => {

                  const isSelected =
                    selectedProject?.proyecto_id ===
                    project.proyecto_id


                  return (

                    <tr
                      key={project.proyecto_id}
                      className={
                        isSelected
                          ? 'project-row-selected'
                          : ''
                      }
                    >

                      <td>

                        <span className="project-id">
                          #{project.proyecto_id}
                        </span>

                      </td>


                      <td>

                        <div className="project-name-cell">

                          <span className="project-avatar">
                            P
                          </span>


                          <div>

                            <strong>
                              {project.nombre}
                            </strong>

                            <small>
                              {project.descripcion ||
                                'Sin descripción'}
                            </small>

                          </div>

                        </div>

                      </td>


                      <td>

                        <span className="models-count-pill">

                          {Number(
                            project.cantidad_modelos || 0
                          )}

                        </span>

                      </td>


                      <td>

                        <span
                          className={
                            project.estado
                              ? 'table-status active'
                              : 'table-status inactive'
                          }
                        >

                          {project.estado
                            ? 'Activo'
                            : 'Inactivo'}

                        </span>

                      </td>


                      <td>

                        {project.fecha_creacion
                          ? new Date(
                              project.fecha_creacion
                            ).toLocaleDateString(
                              'es-CL'
                            )
                          : '-'}

                      </td>


                      <td>

                        <div className="table-actions project-actions">

                          <button
                            type="button"
                            className="table-button view"
                            onClick={() =>
                              loadModels(project)
                            }
                          >
                            Modelos
                          </button>


                          <button
                            type="button"
                            className="table-button edit"
                            onClick={() =>
                              openEditProjectForm(project)
                            }
                          >
                            Editar
                          </button>


                          <button
                            type="button"
                            className={
                              project.estado
                                ? 'table-button deactivate'
                                : 'table-button activate'
                            }
                            onClick={() =>
                              handleProjectStatus(project)
                            }
                          >

                            {project.estado
                              ? 'Desactivar'
                              : 'Reactivar'}

                          </button>

                        </div>

                      </td>

                    </tr>

                  )
                })

              )}

            </tbody>

          </table>

        </div>

      </section>


      {/* ======================================================
          MODELOS DEL PROYECTO
          ====================================================== */}

      {selectedProject && (

        <section className="models-section">


          <div className="models-section-header">

            <div>

              <span className="eyebrow">
                Asociación proyecto-modelo
              </span>


              <h2>
                Modelos de {selectedProject.nombre}
              </h2>


              <p>
                Proyecto #{selectedProject.proyecto_id}.
                Consulta y administra sus modelos
                de datos asociados.
              </p>

            </div>


            <button
              type="button"
              className="primary-button"
              onClick={openCreateModelForm}
              disabled={!selectedProject.estado}
              title={
                !selectedProject.estado
                  ? 'Reactiva el proyecto para agregar modelos'
                  : ''
              }
            >
              + Nuevo modelo
            </button>

          </div>


          {!selectedProject.estado && (

            <div className="project-inactive-notice">

              El proyecto se encuentra inactivo.
              Puedes consultar sus modelos, pero debes
              reactivarlo antes de registrar nuevos modelos.

            </div>

          )}


          {/* ==================================================
              FORMULARIO MODELO
              ================================================== */}

          {modelFormOpen && (

            <section className="model-form-card">

              <div className="project-form-header">

                <div>

                  <span className="eyebrow">

                    {editingModel
                      ? 'Modificar registro'
                      : 'Nuevo modelo'}

                  </span>


                  <h2>

                    {editingModel
                      ? 'Modificar modelo'
                      : 'Crear modelo asociado'}

                  </h2>

                </div>


                <button
                  type="button"
                  className="form-close-button"
                  onClick={closeModelForm}
                >
                  ×
                </button>

              </div>


              <form
                className="project-form"
                onSubmit={handleModelSubmit}
              >

                <label>

                  Nombre del modelo

                  <input
                    name="nombre"
                    value={modelForm.nombre}
                    onChange={handleModelChange}
                    minLength="2"
                    maxLength="150"
                    required
                    placeholder="Ej.: Modelo_Cliente"
                  />

                </label>


                <label>

                  Descripción

                  <textarea
                    name="descripcion"
                    value={modelForm.descripcion}
                    onChange={handleModelChange}
                    maxLength="500"
                    rows="4"
                    placeholder="Describe el contenido del modelo"
                  />

                </label>


                <div className="form-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={closeModelForm}
                  >
                    Cancelar
                  </button>


                  <button
                    type="submit"
                    className="primary-button"
                    disabled={savingModel}
                  >

                    {savingModel
                      ? 'Guardando...'
                      : editingModel
                        ? 'Guardar cambios'
                        : 'Crear modelo'}

                  </button>

                </div>

              </form>

            </section>

          )}


          {/* ==================================================
              TABLA MODELOS
              ================================================== */}

          <section className="models-table-card">

            <div className="projects-table-heading">

              <div>

                <h2>
                  Modelos asociados
                </h2>

                <p>
                  Relación entre el proyecto seleccionado
                  y sus modelos de datos.
                </p>

              </div>


              <span className="projects-count">
                {models.length} registros
              </span>

            </div>


            {loadingModels ? (

              <div className="models-loading">
                Cargando modelos...
              </div>

            ) : (

              <div className="table-responsive">

                <table className="projects-table">

                  <thead>

                    <tr>
                      <th>ID</th>
                      <th>Modelo</th>
                      <th>Proyecto</th>
                      <th>Estado</th>
                      <th>Fecha creación</th>
                      <th>Acciones</th>
                    </tr>

                  </thead>


                  <tbody>

                    {models.length === 0 ? (

                      <tr>

                        <td
                          colSpan="6"
                          className="projects-empty"
                        >
                          Este proyecto todavía no posee
                          modelos asociados.
                        </td>

                      </tr>

                    ) : (

                      models.map((model) => (

                        <tr key={model.modelo_id}>


                          <td>

                            <span className="project-id">
                              #{model.modelo_id}
                            </span>

                          </td>


                          <td>

                            <div className="project-name-cell">

                              <span className="model-avatar">
                                M
                              </span>


                              <div>

                                <strong>
                                  {model.nombre}
                                </strong>

                                <small>
                                  {model.descripcion ||
                                    'Sin descripción'}
                                </small>

                              </div>

                            </div>

                          </td>


                          <td>

                            <span className="project-reference-pill">

                              #{model.proyecto_id}

                            </span>

                          </td>


                          <td>

                            <span
                              className={
                                model.estado
                                  ? 'table-status active'
                                  : 'table-status inactive'
                              }
                            >

                              {model.estado
                                ? 'Activo'
                                : 'Inactivo'}

                            </span>

                          </td>


                          <td>

                            {model.fecha_creacion
                              ? new Date(
                                  model.fecha_creacion
                                ).toLocaleDateString(
                                  'es-CL'
                                )
                              : '-'}

                          </td>


                          <td>

                            <div className="table-actions">

                              <button
                                type="button"
                                className="table-button edit"
                                onClick={() =>
                                  openEditModelForm(model)
                                }
                              >
                                Editar
                              </button>


                              <button
                                type="button"
                                className={
                                  model.estado
                                    ? 'table-button deactivate'
                                    : 'table-button activate'
                                }
                                onClick={() =>
                                  handleModelStatus(model)
                                }
                              >

                                {model.estado
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

            )}

          </section>

        </section>

      )}

    </section>
  )
}