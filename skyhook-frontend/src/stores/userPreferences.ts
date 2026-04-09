import { defineStore } from "pinia"
import { ref } from "vue"

const USER_PREFERENCES_STORAGE_KEY = "skyhook-user-preferences"

export type ThemePreference = "system" | "light" | "dark"
export type NotificationLevel = "all" | "critical" | "silent"

export type UserPreferencesSnapshot = {
  themePreference: ThemePreference
  compactSidebar: boolean
  showSidebarLabels: boolean
  defaultLanding: string
  notificationLevel: NotificationLevel
  notificationSound: boolean
  telemetryAlerts: boolean
  quietHours: string
  callsign: string
}

export const LANDING_PAGE_OPTIONS = [
  { value: "/", label: "Overview" },
  { value: "/narrowband", label: "Narrowband" },
  { value: "/broadband", label: "Broadband" },
  { value: "/ground-station", label: "Ground Station" },
  { value: "/pad-station", label: "Launch Pad Station" },
  { value: "/engine", label: "Engine" },
  { value: "/airbrakes", label: "Airbrakes" },
  { value: "/fins", label: "Fins" },
  { value: "/on-board", label: "On-Board" },
  { value: "/ground-cams", label: "Ground Cameras" },
  { value: "/settings/user", label: "User Settings" },
  { value: "/settings/system", label: "System Settings" },
] as const

const VALID_LANDING_PATHS = new Set<string>(LANDING_PAGE_OPTIONS.map((option) => option.value))

export const DEFAULT_USER_PREFERENCES: UserPreferencesSnapshot = {
  themePreference: "system",
  compactSidebar: false,
  showSidebarLabels: true,
  defaultLanding: "/",
  notificationLevel: "all",
  notificationSound: true,
  telemetryAlerts: true,
  quietHours: "22:00-07:00",
  callsign: "Skyhook Operator",
}

const QUIET_HOURS_PATTERN = /^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$/

export const isValidQuietHours = (value: string) => QUIET_HOURS_PATTERN.test(value.trim())

export const normalizeLandingPath = (value?: string | null) => {
  const next = String(value ?? "").trim()
  return VALID_LANDING_PATHS.has(next) ? next : DEFAULT_USER_PREFERENCES.defaultLanding
}

const normalizeThemePreference = (value?: string | null): ThemePreference => {
  if (value === "light" || value === "dark" || value === "system") return value
  return DEFAULT_USER_PREFERENCES.themePreference
}

const normalizeNotificationLevel = (value?: string | null): NotificationLevel => {
  if (value === "all" || value === "critical" || value === "silent") return value
  return DEFAULT_USER_PREFERENCES.notificationLevel
}

const normalizeCallsign = (value?: string | null) => {
  const next = String(value ?? "").trim()
  return next || DEFAULT_USER_PREFERENCES.callsign
}

const normalizeQuietHours = (value?: string | null) => {
  const next = String(value ?? "").trim()
  return isValidQuietHours(next) ? next : DEFAULT_USER_PREFERENCES.quietHours
}

export const normalizeUserPreferences = (
  raw?: Partial<UserPreferencesSnapshot> | null,
): UserPreferencesSnapshot => ({
  themePreference: normalizeThemePreference(raw?.themePreference),
  compactSidebar: Boolean(raw?.compactSidebar),
  showSidebarLabels: raw?.showSidebarLabels !== false,
  defaultLanding: normalizeLandingPath(raw?.defaultLanding),
  notificationLevel: normalizeNotificationLevel(raw?.notificationLevel),
  notificationSound:
    typeof raw?.notificationSound === "boolean"
      ? raw.notificationSound
      : DEFAULT_USER_PREFERENCES.notificationSound,
  telemetryAlerts:
    typeof raw?.telemetryAlerts === "boolean"
      ? raw.telemetryAlerts
      : DEFAULT_USER_PREFERENCES.telemetryAlerts,
  quietHours: normalizeQuietHours(raw?.quietHours),
  callsign: normalizeCallsign(raw?.callsign),
})

export const isWithinQuietHours = (quietHours: string, at = new Date()) => {
  if (!isValidQuietHours(quietHours)) return false

  const [startText, endText] = quietHours.trim().split("-")
  if (!startText || !endText) return false

  const startParts = startText.split(":")
  const endParts = endText.split(":")
  if (startParts.length !== 2 || endParts.length !== 2) return false

  const startHour = Number(startParts[0])
  const startMinute = Number(startParts[1])
  const endHour = Number(endParts[0])
  const endMinute = Number(endParts[1])
  if (
    Number.isNaN(startHour) ||
    Number.isNaN(startMinute) ||
    Number.isNaN(endHour) ||
    Number.isNaN(endMinute)
  ) {
    return false
  }

  const currentMinutes = at.getHours() * 60 + at.getMinutes()
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute

  if (startMinutes === endMinutes) return true
  if (startMinutes < endMinutes) {
    return currentMinutes >= startMinutes && currentMinutes < endMinutes
  }
  return currentMinutes >= startMinutes || currentMinutes < endMinutes
}

export const useUserPreferencesStore = defineStore("userPreferences", () => {
  const themePreference = ref<ThemePreference>(DEFAULT_USER_PREFERENCES.themePreference)
  const compactSidebar = ref(DEFAULT_USER_PREFERENCES.compactSidebar)
  const showSidebarLabels = ref(DEFAULT_USER_PREFERENCES.showSidebarLabels)
  const defaultLanding = ref(DEFAULT_USER_PREFERENCES.defaultLanding)
  const notificationLevel = ref<NotificationLevel>(DEFAULT_USER_PREFERENCES.notificationLevel)
  const notificationSound = ref(DEFAULT_USER_PREFERENCES.notificationSound)
  const telemetryAlerts = ref(DEFAULT_USER_PREFERENCES.telemetryAlerts)
  const quietHours = ref(DEFAULT_USER_PREFERENCES.quietHours)
  const callsign = ref(DEFAULT_USER_PREFERENCES.callsign)
  const hydrated = ref(false)

  const snapshot = (): UserPreferencesSnapshot => ({
    themePreference: themePreference.value,
    compactSidebar: compactSidebar.value,
    showSidebarLabels: showSidebarLabels.value,
    defaultLanding: defaultLanding.value,
    notificationLevel: notificationLevel.value,
    notificationSound: notificationSound.value,
    telemetryAlerts: telemetryAlerts.value,
    quietHours: quietHours.value,
    callsign: callsign.value,
  })

  const applySnapshot = (next: UserPreferencesSnapshot) => {
    themePreference.value = next.themePreference
    compactSidebar.value = next.compactSidebar
    showSidebarLabels.value = next.showSidebarLabels
    defaultLanding.value = next.defaultLanding
    notificationLevel.value = next.notificationLevel
    notificationSound.value = next.notificationSound
    telemetryAlerts.value = next.telemetryAlerts
    quietHours.value = next.quietHours
    callsign.value = next.callsign
  }

  const persist = () => {
    localStorage.setItem(USER_PREFERENCES_STORAGE_KEY, JSON.stringify(snapshot()))
  }

  const initFromStorage = () => {
    if (hydrated.value) return

    try {
      const raw = localStorage.getItem(USER_PREFERENCES_STORAGE_KEY)
      if (raw) {
        applySnapshot(normalizeUserPreferences(JSON.parse(raw)))
      }
    } catch {
      applySnapshot(DEFAULT_USER_PREFERENCES)
    }

    hydrated.value = true
  }

  const replacePreferences = (next: UserPreferencesSnapshot) => {
    applySnapshot(normalizeUserPreferences(next))
    hydrated.value = true
    persist()
  }

  const updatePreferences = (next: Partial<UserPreferencesSnapshot>) => {
    replacePreferences({ ...snapshot(), ...next })
  }

  const resetToDefaults = () => {
    replacePreferences(DEFAULT_USER_PREFERENCES)
  }

  return {
    themePreference,
    compactSidebar,
    showSidebarLabels,
    defaultLanding,
    notificationLevel,
    notificationSound,
    telemetryAlerts,
    quietHours,
    callsign,
    hydrated,
    initFromStorage,
    snapshot,
    replacePreferences,
    updatePreferences,
    resetToDefaults,
  }
})
