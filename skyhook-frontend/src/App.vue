<script setup lang="ts">
import { RouterView, useRoute } from "vue-router"
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { Toaster } from "@/components/ui/sonner"
import AppHeader from "./components/layout/AppHeader.vue"
import AppSidebar from "@/components/layout/AppSidebar.vue"
import StatusStrip from "@/components/layout/StatusStrip.vue"
import LoginPage from "@/components/auth/LoginPage.vue"
import { socket } from "@/socket"
import { notify } from "@/lib/notifications"
import { WifiOffIcon } from "lucide-vue-next"
import { useCommsStore } from "@/stores/comms"
import { storeToRefs } from "pinia"

const route = useRoute()
const THEME_STORAGE_KEY = "skyhook-theme"
const AUTH_STORAGE_KEY = "skyhook-auth"
const AUTH_EMAIL_STORAGE_KEY = "skyhook-auth-email"
const isDark = ref(false)
const isAuthenticated = ref(false)
const loginLoading = ref(false)
const loginError = ref<string | null>(null)
const userName = ref("Skyhook Administrator")
const userEmail = ref("username@tu-berlin.de")

const comms = useCommsStore()
const { nb, bb } = storeToRefs(comms)

const formatBps = (bps: number | null | undefined): string => {
  if (bps == null || Number.isNaN(bps)) return "n/a"
  if (Math.abs(bps) >= 1_000_000) return `${(bps / 1_000_000).toFixed(1)} Mb/s`
  if (Math.abs(bps) >= 1_000) return `${(bps / 1_000).toFixed(1)} kb/s`
  return `${bps.toFixed(0)} b/s`
}

const uplinkSpeed = computed(() => formatBps(nb.value.up.rateBps.value))
const nbSpeed = computed(() => formatBps(nb.value.down.rateBps.value))
const bbSpeed = computed(() => formatBps(bb.value.down.rateBps.value))
const wsStatus = ref(socket.connected ? "Online" : "Offline")
const wsBadgeClass = computed(() => {
  if (wsStatus.value === "Online") {
    return "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
  }
  if (wsStatus.value === "Connecting..." || wsStatus.value === "Reconnecting...") {
    return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
  }
  return "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
})

const applyTheme = (dark: boolean) => {
  isDark.value = dark
  const root = document.documentElement
  root.classList.toggle("dark", dark)
  localStorage.setItem(THEME_STORAGE_KEY, dark ? "dark" : "light")
}

const toggleTheme = () => applyTheme(!isDark.value)

type LoginPayload = {
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

const handleLogin = async ({ email, password, remember }: LoginPayload) => {
  loginError.value = null
  if (!email || !password) {
    loginError.value = "Email and password are required."
    return
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
  } catch (error) {
    console.error(error)
    loginError.value = "Unable to sign in right now. Please try again."
  } finally {
    loginLoading.value = false
  }
}

const handleSignOut = () => {
  isAuthenticated.value = false
  localStorage.removeItem(AUTH_STORAGE_KEY)
  localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY)
  notify({ title: "Signed out", description: "Session closed.", variant: "info" })
}

onMounted(() => {
  const storedPreference = localStorage.getItem(THEME_STORAGE_KEY)
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
  applyTheme(storedPreference ? storedPreference === "dark" : prefersDark)

  const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY)
  if (storedAuth === "true") {
    isAuthenticated.value = true
    const savedEmail = localStorage.getItem(AUTH_EMAIL_STORAGE_KEY)
    if (savedEmail) {
      userEmail.value = savedEmail
      userName.value = deriveNameFromEmail(savedEmail)
    }
  }
})

onMounted(() => {
  let hasShownDisconnect = false

  const showDisconnected = () => {
    if (!hasShownDisconnect || !isAuthenticated.value) {
      if (!isAuthenticated.value) {
        hasShownDisconnect = false
        return
      }
      notify({
        title: "Disconnected from server",
        description: "You have been disconnected from the server. Please check your network connection, and validate that the server is running.",
        variant: "error",
        icon: WifiOffIcon,
      })
      hasShownDisconnect = true
    }
  }

  const showReconnected = () => {
    if (hasShownDisconnect && isAuthenticated.value) {
      notify({
        title: "Connection restored",
        description: "Reconnected to the server.",
        variant: "default",
      })
      hasShownDisconnect = false
    }
  }

  const setOnline = () => {
    wsStatus.value = "Online"
    showReconnected()
  }

  const setOffline = () => {
    wsStatus.value = "Offline"
    showDisconnected()
  }

  const setReconnecting = () => {
    wsStatus.value = "Reconnecting..."
  }

  wsStatus.value = socket.connected ? "Online" : "Connecting..."
  socket.on("connect", setOnline)
  socket.on("disconnect", setOffline)
  socket.on("connect_error", setOffline)
  socket.io.on("reconnect_attempt", setReconnecting)
  socket.io.on("reconnect", setOnline)
  socket.io.on("reconnect_error", setOffline)
})

onBeforeUnmount(() => {
  socket.off("connect")
  socket.off("disconnect")
  socket.off("connect_error")
  socket.io.off("reconnect_attempt")
  socket.io.off("reconnect")
  socket.io.off("reconnect_error")
})
</script>

<template>
  <div class="h-svh w-full bg-background text-foreground">
    <LoginPage
      v-if="!isAuthenticated"
      :loading="loginLoading"
      :error="loginError"
      :default-email="userEmail"
      @submit="handleLogin"
    />

    <SidebarProvider v-else class="h-svh overflow-hidden">
      <AppSidebar
        :current-route-name="route.name ? String(route.name) : null"
        :is-dark="isDark"
        :user-name="userName"
        :user-email="userEmail"
        @toggle-theme="toggleTheme"
        @sign-out="handleSignOut"
      />

      <SidebarInset class="h-svh pb-12 flex flex-col bg-muted/20 overflow-hidden">
        <!-- top header bar -->
        <AppHeader
          :route-name="route.name ? String(route.name) : null"
          :ws-status="wsStatus"
          :ws-badge-class="wsBadgeClass"
        />

        <!-- page content wrapper -->
        <main class="flex-1 min-h-0 overflow-auto">
          <div class="mx-auto max-w-6xl p-4 md:p-6">
            <RouterView />
          </div>
        </main>
      </SidebarInset>

      <!-- bottom status strip: slightly more “polished” -->
      <StatusStrip :uplink-speed="uplinkSpeed" :nb-speed="nbSpeed" :bb-speed="bbSpeed" />
    </SidebarProvider>

    <Toaster :theme="isDark ? 'dark' : 'light'" rich-colors />
  </div>
</template>
