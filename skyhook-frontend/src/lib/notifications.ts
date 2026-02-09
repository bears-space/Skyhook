import { toast } from "vue-sonner"

export type NotificationVariant = "default" | "success" | "info" | "warning" | "error" | "destructive"

export type NotificationAction = {
  label: string
  onClick: () => void
}

export type NotificationOptions = {
  title: string
  description?: string
  variant?: NotificationVariant
  timeout?: number
  icon?: unknown
  showClose?: boolean
  className?: string
  color?: string
  background?: string
  textColor?: string
  borderColor?: string
  action?: NotificationAction
  id?: string | number
}

type ToastOptions = {
  description?: string
  duration?: number
  icon?: any
  closeButton?: boolean
  className?: string
  style?: Record<string, string>
  action?: NotificationAction
  id?: string | number
}

const buildStyle = (options: NotificationOptions) => {
  const style: Record<string, string> = {}

  if (options.background) {
    style.background = options.background
  } else if (options.color) {
    style.background = options.color
  }

  if (options.textColor) {
    style.color = options.textColor
  }

  if (options.borderColor) {
    style.borderColor = options.borderColor
  }

  return Object.keys(style).length ? style : undefined
}

const getToastFn = (variant?: NotificationVariant) => {
  switch (variant) {
    case "success":
      return toast.success
    case "info":
      return toast.info
    case "warning":
      return toast.warning
    case "error":
    case "destructive":
      return toast.error
    default:
      return toast
  }
}

export const notify = (options: NotificationOptions) => {
  const {
    title,
    description,
    timeout,
    icon,
    showClose,
    className,
    action,
    id,
  } = options

  const toastOptions: ToastOptions = {
    description,
    duration: timeout,
    icon,
    className,
    action,
    id,
  }

  const style = buildStyle(options)
  if (style) {
    toastOptions.style = style
  }

  if (showClose !== undefined) {
    toastOptions.closeButton = showClose
  }

  return getToastFn(options.variant)(title, toastOptions)
}

export const dismissNotification = (id?: string | number) => {
  toast.dismiss(id)
}

export const notifySuccess = (options: Omit<NotificationOptions, "variant">) =>
  notify({ ...options, variant: "success" })

export const notifyInfo = (options: Omit<NotificationOptions, "variant">) =>
  notify({ ...options, variant: "info" })

export const notifyWarning = (options: Omit<NotificationOptions, "variant">) =>
  notify({ ...options, variant: "warning" })

export const notifyError = (options: Omit<NotificationOptions, "variant">) =>
  notify({ ...options, variant: "error" })
