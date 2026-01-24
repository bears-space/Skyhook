import { inject, reactive, readonly } from "vue"

const ALERT_KEY = Symbol("alert-service")

const DEFAULT_DURATION = 4000

const createService = () => {
  const alerts = reactive([])
  let nextId = 1

  const remove = (id) => {
    const idx = alerts.findIndex((a) => a.id === id)
    if (idx !== -1) alerts.splice(idx, 1)
  }

  const show = ({
    title,
    description,
    variant = "default",
    duration = DEFAULT_DURATION,
    icon = null,
  }) => {
    const id = nextId++
    alerts.push({ id, title, description, variant, icon })
    if (duration !== 0) {
      setTimeout(() => remove(id), duration)
    }
    return id
  }

  return {
    alerts: readonly(alerts),
    show,
    remove,
  }
}

export const alertsPlugin = {
  install(app) {
    const service = createService()
    app.provide(ALERT_KEY, service)
    app.config.globalProperties.$alert = service.show
  },
}

export const useAlerts = () => {
  const service = inject(ALERT_KEY)
  if (!service) {
    throw new Error("Alert service not available. Did you forget to install alertsPlugin?")
  }
  return service
}
