import { defineStore } from "pinia"
import { ref } from "vue"
import { notify } from "@/lib/notifications"
import { setSocketAuthToken, socket } from "@/socket"

const AUTH_STORAGE_KEY = "skyhook-auth"
const AUTH_EMAIL_STORAGE_KEY = "skyhook-auth-email"
const AUTH_TOKEN_STORAGE_KEY = "skyhook-auth-token"
const API_BASE =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "http://localhost:3000" : "")

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
  const token = ref<string | null>(null)
  const loginLoading = ref(false)
  const loginError = ref<string | null>(null)
  const hydrated = ref(false)

  const initFromStorage = () => {
    if (hydrated.value) return
    const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY)
    const storedToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    if (storedAuth === "true" && storedToken) {
      isAuthenticated.value = true
      token.value = storedToken
      const savedEmail = localStorage.getItem(AUTH_EMAIL_STORAGE_KEY)
      if (savedEmail) {
        userEmail.value = savedEmail
        userName.value = deriveNameFromEmail(savedEmail)
      }
      // ensure socket auth is hydrated for reconnect
      setSocketAuthToken(storedToken)
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
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        loginError.value = data.error || "Invalid credentials"
        return false
      }

      const data = await response.json()
      const receivedToken = data.token as string | undefined
      if (!receivedToken) {
        loginError.value = "No token returned from server."
        return false
      }

      isAuthenticated.value = true
      userEmail.value = email
      userName.value = deriveNameFromEmail(email)
      token.value = receivedToken
      setSocketAuthToken(receivedToken)
      if (!socket.connected) {
        socket.connect()
      }

      if (remember) {
        localStorage.setItem(AUTH_STORAGE_KEY, "true")
        localStorage.setItem(AUTH_EMAIL_STORAGE_KEY, email)
        localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, receivedToken)
      } else {
        localStorage.removeItem(AUTH_STORAGE_KEY)
        localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY)
        localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
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
    token.value = null
    localStorage.removeItem(AUTH_STORAGE_KEY)
    localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY)
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
    setSocketAuthToken(undefined)
    socket.disconnect()
    notify({ title: "Signed out", description: "Session closed.", variant: "info" })
  }

  return {
    isAuthenticated,
    userName,
    userEmail,
    token,
    loginLoading,
    loginError,
    hydrated,
    initFromStorage,
    login,
    signOut,
  }
})
