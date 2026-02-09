import { defineStore } from "pinia"
import { ref } from "vue"
import { notify } from "@/lib/notifications"

const AUTH_STORAGE_KEY = "skyhook-auth"
const AUTH_EMAIL_STORAGE_KEY = "skyhook-auth-email"

export type LoginPayload = {
  email: string
  password: string
  remember: boolean
}

const deriveNameFromEmail = (email: string): string => {
  const namePart = email.split("@")[0] ?? ""
  if (!namePart) return "Skyhook Operator"
  return namePart
    .replace(/[._-]+/g, " ")
    .trim()
    .split(" ")
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ")
}

export const useAuthStore = defineStore("auth", () => {
  const isAuthenticated = ref(false)
  const userName = ref("Skyhook Administrator")
  const userEmail = ref("username@tu-berlin.de")
  const loginLoading = ref(false)
  const loginError = ref<string | null>(null)
  const hydrated = ref(false)

  const initFromStorage = () => {
    if (hydrated.value) return
    const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY)
    if (storedAuth === "true") {
      isAuthenticated.value = true
      const savedEmail = localStorage.getItem(AUTH_EMAIL_STORAGE_KEY)
      if (savedEmail) {
        userEmail.value = savedEmail
        userName.value = deriveNameFromEmail(savedEmail)
      }
    }
    hydrated.value = true
  }

  const login = async ({ email, password, remember }: LoginPayload) => {
    loginError.value = null
    if (!email || !password) {
      loginError.value = "Email and password are required."
      return false
    }

    loginLoading.value = true
    try {
      await new Promise((resolve) => setTimeout(resolve, 450))
      isAuthenticated.value = true
      userEmail.value = email
      userName.value = deriveNameFromEmail(email)

      if (remember) {
        localStorage.setItem(AUTH_STORAGE_KEY, "true")
        localStorage.setItem(AUTH_EMAIL_STORAGE_KEY, email)
      } else {
        localStorage.removeItem(AUTH_STORAGE_KEY)
        localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY)
      }

      notify({
        title: "Signed in",
        description: "Welcome back to Skyhook Mission Control.",
        variant: "success",
      })
      return true
    } catch (error) {
      console.error(error)
      loginError.value = "Unable to sign in right now. Please try again."
      return false
    } finally {
      loginLoading.value = false
    }
  }

  const signOut = () => {
    isAuthenticated.value = false
    localStorage.removeItem(AUTH_STORAGE_KEY)
    localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY)
    notify({ title: "Signed out", description: "Session closed.", variant: "info" })
  }

  return {
    isAuthenticated,
    userName,
    userEmail,
    loginLoading,
    loginError,
    hydrated,
    initFromStorage,
    login,
    signOut,
  }
})
