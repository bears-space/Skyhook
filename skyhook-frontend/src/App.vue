<script setup lang="ts">
import { RouterView, useRoute, useRouter } from "vue-router"
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { Toaster } from "@/components/ui/sonner"
import AppHeader from "./components/layout/AppHeader.vue"
import AppSidebar from "@/components/layout/AppSidebar.vue"
import StatusStrip from "@/components/layout/StatusStrip.vue"
import { socket } from "@/socket"
import { notify } from "@/lib/notifications"
import { WifiOffIcon } from "lucide-vue-next"
import { useCommsStore } from "@/stores/comms"
import { storeToRefs } from "pinia"
import { useAuthStore } from "@/stores/auth"
import { useUserPreferencesStore } from "@/stores/userPreferences"

const route = useRoute()
const router = useRouter()
const isDark = ref(false)
const auth = useAuthStore()
const { isAuthenticated, userName, userEmail } = storeToRefs(auth)
const preferences = useUserPreferencesStore()
const { themePreference, compactSidebar, showSidebarLabels, callsign } = storeToRefs(preferences)

const comms = useCommsStore()
const { nb, bb } = storeToRefs(comms)
let themeMediaQuery: MediaQueryList | null = null
let removeThemeListener: (() => void) | null = null

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
  document.documentElement.classList.toggle("dark", dark)
}

const syncThemeFromPreference = () => {
  const prefersDark = themeMediaQuery?.matches ?? window.matchMedia("(prefers-color-scheme: dark)").matches
  applyTheme(themePreference.value === "dark" || (themePreference.value === "system" && prefersDark))
}

const toggleTheme = () => {
  preferences.updatePreferences({
    themePreference: isDark.value ? "light" : "dark",
  })
}

const handleSignOut = () => {
  auth.signOut()
  router.replace({ path: "/login", query: { redirect: route.fullPath } })
}

const sidebarDisplayName = computed(() => callsign.value.trim() || userName.value || "Skyhook Operator")

onMounted(() => {
  preferences.initFromStorage()
  auth.initFromStorage()
  themeMediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
  const handleThemeChange = () => {
    if (themePreference.value === "system") {
      syncThemeFromPreference()
    }
  }
  themeMediaQuery.addEventListener("change", handleThemeChange)
  removeThemeListener = () => themeMediaQuery?.removeEventListener("change", handleThemeChange)
  syncThemeFromPreference()
})

watch(themePreference, () => {
  syncThemeFromPreference()
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
  removeThemeListener?.()
  removeThemeListener = null
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
    <RouterView v-slot="{ Component, route: currentRoute }">
      <component :is="Component" v-if="currentRoute.meta?.layout === 'auth'" />

      <SidebarProvider
        v-else
        class="h-svh overflow-hidden"
        :open="showSidebarLabels"
        @update:open="preferences.updatePreferences({ showSidebarLabels: $event })"
      >
        <AppSidebar
          :current-route-name="route.name ? String(route.name) : null"
          :is-dark="isDark"
          :compact="compactSidebar"
          :show-labels="showSidebarLabels"
          :user-name="sidebarDisplayName"
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
              <component :is="Component" />
            </div>
          </main>
        </SidebarInset>

        <!-- bottom status strip: slightly more “polished” -->
        <StatusStrip :uplink-speed="uplinkSpeed" :nb-speed="nbSpeed" :bb-speed="bbSpeed" />
      </SidebarProvider>
    </RouterView>

    <Toaster :theme="isDark ? 'dark' : 'light'" rich-colors />
  </div>
</template>
