import { useFeedback } from '../components/FeedbackProvider'
import { useEffect, useMemo, useState } from 'react'
import {
  createUser,
  getRoles,
  getUsers,
  updateUser,
  updateUserStatus,
} from '../api/users'


const initialForm = {
  nombre: '',
  apellido: '',
  email: '',
  password: '',
  rol_id: '',
}


export default function UsersPage({ currentUser }) {
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { confirmAction, notifySuccess } = useFeedback()


  const [formOpen, setFormOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)

  const [form, setForm] = useState(initialForm)


  useEffect(() => {
    loadData()
  }, [])


  async function loadData() {
    setLoading(true)
    setError('')

    try {
      const [usersData, rolesData] = await Promise.all([
        getUsers(),
        getRoles(),
      ])

      setUsers(usersData)
      setRoles(rolesData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }


  function openCreateForm() {
    setEditingUser(null)

    setForm({
      ...initialForm,
      rol_id: roles.length > 0
        ? String(roles[0].rol_id)
        : '',
    })

    setError('')
    setSuccess('')
    setFormOpen(true)
  }


  function openEditForm(user) {
    setEditingUser(user)

    setForm({
      nombre: user.nombre,
      apellido: user.apellido,
      email: user.email,
      password: '',
      rol_id: String(user.rol_id),
    })

    setError('')
    setSuccess('')
    setFormOpen(true)
  }


  function closeForm() {
    setFormOpen(false)
    setEditingUser(null)
    setForm(initialForm)
    setError('')
  }


  function handleChange(event) {
    const { name, value } = event.target

    setForm((current) => ({
      ...current,
      [name]: value,
    }))
  }


  async function handleSubmit(event) {
    event.preventDefault()

    const accepted = await confirmAction({
      title: editingUser
        ? `¿Guardar los cambios de ${form.nombre} ${form.apellido}?`
        : `¿Crear el usuario ${form.nombre} ${form.apellido}?`,
      description: 'Los datos se guardarán en TestData Studio.',
      confirmText: editingUser ? 'Guardar cambios' : 'Crear usuario',
      cancelText: 'Volver al formulario',
      summary: [{ label: 'Usuario', value: `${form.nombre} ${form.apellido}` }, { label: 'Correo', value: form.email }],
    })
    if (!accepted) return

    setSaving(true)
    setError('')
    setSuccess('')

    try {
      if (editingUser) {
        const payload = {
          nombre: form.nombre,
          apellido: form.apellido,
          email: form.email,
          rol_id: Number(form.rol_id),
          password: form.password.trim()
            ? form.password
            : null,
        }

        const updated = await updateUser(
          editingUser.usuario_id,
          payload,
        )

        setUsers((current) =>
          current.map((user) =>
            user.usuario_id === updated.usuario_id
              ? updated
              : user
          )
        )

        notifySuccess('Usuario modificado correctamente.')
      } else {
        const payload = {
          nombre: form.nombre,
          apellido: form.apellido,
          email: form.email,
          password: form.password,
          rol_id: Number(form.rol_id),
        }

        const created = await createUser(payload)

        setUsers((current) => [
          ...current,
          created,
        ])

        notifySuccess('Usuario creado correctamente.')
      }

      setFormOpen(false)
      setEditingUser(null)
      setForm(initialForm)

    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }


  async function handleStatus(user) {
    const newStatus = !user.estado

    const action = newStatus
      ? 'reactivar'
      : 'desactivar'

    const confirmed = await confirmAction({
      title: `¿Deseas ${action} al usuario ${user.nombre} ${user.apellido}?`,
      description: 'Se actualizará el estado del usuario en TestData Studio.',
      confirmText: newStatus ? 'Reactivar usuario' : 'Desactivar usuario',
      summary: [{ label: 'Usuario', value: `${user.nombre} ${user.apellido}` }, { label: 'Nuevo estado', value: newStatus ? 'Activo' : 'Inactivo' }],
    })

    if (!confirmed) {
      return
    }

    setError('')
    setSuccess('')

    try {
      const updated = await updateUserStatus(
        user.usuario_id,
        newStatus,
      )

      setUsers((current) =>
        current.map((item) =>
          item.usuario_id === updated.usuario_id
            ? updated
            : item
        )
      )

      notifySuccess(
        newStatus
          ? 'Usuario reactivado correctamente.'
          : 'Usuario desactivado correctamente.'
      )

    } catch (err) {
      setError(err.message)
    }
  }


  const activeUsers = useMemo(
    () => users.filter((user) => user.estado).length,
    [users]
  )


  if (loading) {
    return (
      <div className="users-loading">
        Cargando usuarios...
      </div>
    )
  }


  return (
    <section className="users-page">

      <header className="users-header">
        <div>
          <span className="eyebrow">
            Administración
          </span>

          <h1>Gestión de usuarios</h1>

          <p>
            Administra las cuentas, perfiles y estados
            de acceso a TestData Studio.
          </p>
        </div>

        <button
          type="button"
          className="primary-button users-new-button"
          onClick={openCreateForm}
        >
          + Nuevo usuario
        </button>
      </header>


      <section className="users-summary">

        <article className="users-summary-card">
          <span>Total usuarios</span>
          <strong>{users.length}</strong>
        </article>

        <article className="users-summary-card active">
          <span>Activos</span>
          <strong>{activeUsers}</strong>
        </article>

        <article className="users-summary-card inactive">
          <span>Inactivos</span>
          <strong>{users.length - activeUsers}</strong>
        </article>

        <article className="users-summary-card roles">
          <span>Perfiles</span>
          <strong>{roles.length}</strong>
        </article>

      </section>


      {error && (
        <div className="users-message error">
          {error}
        </div>
      )}


{formOpen && (
        <section className="user-form-card">

          <div className="user-form-header">
            <div>
              <span className="eyebrow">
                {editingUser
                  ? 'Modificar registro'
                  : 'Nuevo registro'}
              </span>

              <h2>
                {editingUser
                  ? 'Modificar usuario'
                  : 'Crear usuario'}
              </h2>
            </div>

            <button
              type="button"
              className="form-close-button"
              onClick={closeForm}
            >
              ×
            </button>
          </div>


          <form
            className="user-form"
            onSubmit={handleSubmit}
          >

            <label>
              Nombre

              <input
                name="nombre"
                value={form.nombre}
                onChange={handleChange}
                minLength="2"
                maxLength="100"
                required
              />
            </label>


            <label>
              Apellido

              <input
                name="apellido"
                value={form.apellido}
                onChange={handleChange}
                minLength="2"
                maxLength="100"
                required
              />
            </label>


            <label className="form-wide">
              Correo electrónico

              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                maxLength="150"
                required
              />
            </label>


            <label>
              Perfil

              <select
                name="rol_id"
                value={form.rol_id}
                onChange={handleChange}
                required
              >
                <option value="">
                  Seleccionar perfil
                </option>

                {roles.map((role) => (
                  <option
                    key={role.rol_id}
                    value={role.rol_id}
                  >
                    {role.nombre}
                  </option>
                ))}
              </select>
            </label>


            <label>
              {editingUser
                ? 'Nueva contraseña'
                : 'Contraseña'}

              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                minLength="8"
                required={!editingUser}
                placeholder={
                  editingUser
                    ? 'Dejar vacío para conservar'
                    : 'Mínimo 8 caracteres'
                }
              />

              {editingUser && (
                <small>
                  Si no deseas cambiarla, deja este
                  campo vacío.
                </small>
              )}
            </label>


            <div className="form-actions form-wide">

              <button
                type="button"
                className="secondary-button"
                onClick={closeForm}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={saving}
              >
                {saving
                  ? 'Guardando...'
                  : editingUser
                    ? 'Guardar cambios'
                    : 'Crear usuario'}
              </button>

            </div>

          </form>

        </section>
      )}


      <section className="users-table-card">

        <div className="users-table-heading">
          <div>
            <h2>Usuarios registrados</h2>

            <p>
              Cuentas disponibles en la plataforma.
            </p>
          </div>

          <span className="users-count">
            {users.length} registros
          </span>
        </div>


        <div className="table-responsive">

          <table className="users-table">

            <thead>
              <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Correo</th>
                <th>Perfil</th>
                <th>Estado</th>
                <th>Fecha creación</th>
                <th>Acciones</th>
              </tr>
            </thead>

            <tbody>

              {users.map((user) => {

                const isCurrentUser =
                  user.usuario_id === currentUser?.usuario_id

                return (
                  <tr key={user.usuario_id}>

                    <td>
                      <span className="user-id">
                        #{user.usuario_id}
                      </span>
                    </td>

                    <td>
                      <div className="user-name-cell">
                        <span className="user-avatar">
                          {user.nombre
                            ?.charAt(0)
                            .toUpperCase()}
                        </span>

                        <div>
                          <strong>
                            {user.nombre} {user.apellido}
                          </strong>

                          {isCurrentUser && (
                            <small>
                              Sesión actual
                            </small>
                          )}
                        </div>
                      </div>
                    </td>

                    <td>
                      {user.email}
                    </td>

                    <td>
                      <span className="role-pill">
                        {user.rol}
                      </span>
                    </td>

                    <td>
                      <span
                        className={
                          user.estado
                            ? 'table-status active'
                            : 'table-status inactive'
                        }
                      >
                        {user.estado
                          ? 'Activo'
                          : 'Inactivo'}
                      </span>
                    </td>

                    <td>
                      {user.fecha_creacion
                        ? new Date(
                            user.fecha_creacion
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
                            openEditForm(user)
                          }
                        >
                          Editar
                        </button>

                        <button
                          type="button"
                          className={
                            user.estado
                              ? 'table-button deactivate'
                              : 'table-button activate'
                          }
                          disabled={isCurrentUser}
                          title={
                            isCurrentUser
                              ? 'No puedes modificar el estado de tu propia sesión'
                              : ''
                          }
                          onClick={() =>
                            handleStatus(user)
                          }
                        >
                          {user.estado
                            ? 'Desactivar'
                            : 'Reactivar'}
                        </button>

                      </div>
                    </td>

                  </tr>
                )
              })}

            </tbody>

          </table>

        </div>

      </section>

    </section>
  )
}