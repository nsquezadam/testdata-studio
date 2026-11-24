import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

/**
 * Feedback transversal de TestData Studio.
 * Conserva el mismo estilo que las confirmaciones y avisos de M04.
 * No realiza peticiones a la API: cada vista conserva su lógica de negocio.
 */
const FeedbackContext = createContext(null)

function FeedbackToast({ notice, onClose }) {
  useEffect(() => {
    const timer = window.setTimeout(() => onClose(notice.id), 4300)
    return () => window.clearTimeout(timer)
  }, [notice.id, onClose])

  const error = notice.kind === 'error'
  return (
    <div className={`execution-toast ${error ? 'error' : 'success'}`} role={error ? 'alert' : 'status'}>
      <span className="execution-toast-icon" aria-hidden="true">{error ? '!' : '✓'}</span>
      <div>
        <strong>{error ? 'No se pudo completar la operación' : 'Operación completada'}</strong>
        <p>{notice.message}</p>
      </div>
      <button type="button" onClick={() => onClose(notice.id)} aria-label="Cerrar aviso">×</button>
    </div>
  )
}

export function FeedbackProvider({ children }) {
  const [dialog, setDialog] = useState(null)
  const [notices, setNotices] = useState([])
  const pending = useRef(null)
  const lastFocus = useRef(null)
  const confirmButton = useRef(null)
  const nextId = useRef(0)

  const dismissNotice = useCallback((id) => {
    setNotices((items) => items.filter((item) => item.id !== id))
  }, [])

  const notify = useCallback((message, kind = 'success') => {
    if (!message) return
    const id = ++nextId.current
    setNotices((items) => [...items.slice(-2), { id, kind, message: String(message) }])
  }, [])

  const notifySuccess = useCallback((message) => notify(message, 'success'), [notify])
  const notifyError = useCallback((message) => notify(message, 'error'), [notify])

  const confirmAction = useCallback((options = {}) => {
    // Evita que dos envíos rápidos abran confirmaciones superpuestas.
    if (pending.current) return Promise.resolve(false)
    return new Promise((resolve) => {
      lastFocus.current = document.activeElement
      pending.current = resolve
      setDialog({
        title: options.title || '¿Confirmar esta acción?',
        description: options.description || 'Revisa los datos antes de continuar.',
        confirmText: options.confirmText || 'Confirmar',
        cancelText: options.cancelText || 'Cancelar',
        actionLabel: options.actionLabel || 'Confirmar operación',
        summary: Array.isArray(options.summary) ? options.summary : [],
      })
    })
  }, [])

  const resolveDialog = useCallback((accepted) => {
    const resolve = pending.current
    pending.current = null
    setDialog(null)
    if (resolve) resolve(accepted)
    requestAnimationFrame(() => lastFocus.current?.focus?.())
  }, [])

  useEffect(() => {
    if (!dialog) return undefined
    confirmButton.current?.focus()
    function onKeyDown(event) {
      if (event.key === 'Escape') {
        event.preventDefault()
        resolveDialog(false)
      }
      if (event.key === 'Tab') {
        const buttons = Array.from(document.querySelectorAll('[data-feedback-dialog] button'))
        if (!buttons.length) return
        const first = buttons[0]
        const last = buttons[buttons.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [dialog, resolveDialog])

  useEffect(() => () => {
    if (pending.current) pending.current(false)
    pending.current = null
  }, [])

  return (
    <FeedbackContext.Provider value={{ confirmAction, notifySuccess, notifyError }}>
      {children}
      {typeof document !== 'undefined' && createPortal(
        <>
          {notices.length > 0 && (
            <div className="execution-toast-stack" aria-live="polite">
              {notices.map((notice) => (
                <FeedbackToast key={notice.id} notice={notice} onClose={dismissNotice} />
              ))}
            </div>
          )}
          {dialog && (
            <div className="execution-modal-backdrop" role="presentation" onMouseDown={(event) => {
              if (event.target === event.currentTarget) resolveDialog(false)
            }}>
              <section data-feedback-dialog className="execution-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="app-feedback-title" aria-describedby="app-feedback-description">
                <div className="execution-confirm-icon" aria-hidden="true">✓</div>
                <div className="execution-confirm-heading">
                  <span className="eyebrow">{dialog.actionLabel}</span>
                  <h3 id="app-feedback-title">{dialog.title}</h3>
                  <p id="app-feedback-description">{dialog.description}</p>
                </div>
                {dialog.summary.length > 0 && (
                  <div className="execution-confirm-summary">
                    {dialog.summary.map(({ label, value }, index) => (
                      <div key={`${index}-${label}`}>
                        <span>{label}</span>
                        <strong>{value ?? '—'}</strong>
                      </div>
                    ))}
                  </div>
                )}
                <div className="execution-confirm-actions">
                  <button type="button" className="execution-secondary-button" onClick={() => resolveDialog(false)}>{dialog.cancelText}</button>
                  <button type="button" ref={confirmButton} className="execution-confirm-button" onClick={() => resolveDialog(true)}>{dialog.confirmText}</button>
                </div>
              </section>
            </div>
          )}
        </>, document.body,
      )}
    </FeedbackContext.Provider>
  )
}

export function useFeedback() {
  const feedback = useContext(FeedbackContext)
  if (!feedback) throw new Error('useFeedback debe utilizarse dentro de FeedbackProvider')
  return feedback
}
