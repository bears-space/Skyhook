<script setup lang="ts">
import { RouterView, useRoute } from "vue-router"
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
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

const route = useRoute()
const THEME_STORAGE_KEY = "skyhook-theme"
const isDark = ref(false)

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

onMounted(() => {
  const storedPreference = localStorage.getItem(THEME_STORAGE_KEY)
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
  applyTheme(storedPreference ? storedPreference === "dark" : prefersDark)
})

onMounted(() => {
  let hasShownDisconnect = false

  const showDisconnected = () => {
    if (!hasShownDisconnect) {
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
    if (hasShownDisconnect) {
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
  <SidebarProvider class="h-svh overflow-hidden">
    <AppSidebar
      :current-route-name="route.name ? String(route.name) : null"
      :is-dark="isDark"
      @toggle-theme="toggleTheme"
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

    <Toaster :theme="isDark ? 'dark' : 'light'" rich-colors/> <!-- why is this dark mode shit even needed, shouldnt it do that automatically? -->
  </SidebarProvider>
</template>
