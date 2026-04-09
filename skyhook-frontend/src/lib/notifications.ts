import { getActivePinia } from "pinia"
import { toast } from "vue-sonner"
import { isWithinQuietHours, useUserPreferencesStore } from "@/stores/userPreferences"

export type NotificationVariant = "default" | "success" | "info" | "warning" | "error" | "destructive"
export type NotificationChannel = "auth" | "system" | "telemetry" | "user"

export type NotificationAction = {
  label: string
  onClick: () => void
}

export type NotificationOptions = {
  title: string
  description?: string
  variant?: NotificationVariant
  channel?: NotificationChannel
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

const getPreferences = () => {
  const pinia = getActivePinia()
  if (!pinia) return null

  try {
    const preferences = useUserPreferencesStore(pinia)
    preferences.initFromStorage()
    return preferences
  } catch {
    return null
  }
}

const isCriticalNotification = (variant?: NotificationVariant) =>
  variant === "warning" || variant === "error" || variant === "destructive"

const shouldSuppressNotification = (options: NotificationOptions) => {
  const preferences = getPreferences()
  if (!preferences) return false
  if (options.channel === "user") return false

  if (options.channel === "telemetry" && !preferences.telemetryAlerts) {
    return true
  }

  if (preferences.notificationLevel === "silent") {
    return true
  }

  if (preferences.notificationLevel === "critical" && !isCriticalNotification(options.variant)) {
    return true
  }

  return false
}

const shouldPlaySound = (options: NotificationOptions) => {
  const preferences = getPreferences()
  if (!preferences || !preferences.notificationSound) return false
  if (!isCriticalNotification(options.variant)) return false
  if (options.channel === "telemetry" && !preferences.telemetryAlerts) return false
  return !isWithinQuietHours(preferences.quietHours)
}

let audioContext: AudioContext | null = null

const playNotificationTone = () => {
  if (typeof window === "undefined") return

  const AudioContextCtor =
    window.AudioContext || (window as Window & typeof globalThis & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AudioContextCtor) return

  try {
    audioContext ??= new AudioContextCtor()
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    oscillator.type = "triangle"
    oscillator.frequency.value = 880
    gain.gain.value = 0.03
    oscillator.connect(gain)
    gain.connect(audioContext.destination)
    oscillator.start()
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.18)
    oscillator.stop(audioContext.currentTime + 0.18)
  } catch {
    // Best-effort enhancement only.
  }
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
  if (shouldSuppressNotification(options)) {
    return undefined
  }

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

  if (shouldPlaySound(options)) {
    playNotificationTone()
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
