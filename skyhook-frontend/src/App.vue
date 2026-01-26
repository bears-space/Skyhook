<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from "vue-router"
import { computed, onBeforeUnmount, onMounted, ref, type Component } from "vue"
import Badge from "@/components/ui/badge/Badge.vue"
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  Camera,
  Cctv,
  ChevronsLeftRightEllipsis,
  FlameIcon,
  GamepadDirectional,
  HardDriveDownload,
  LayoutDashboard,
  Moon,
  RadioTower,
  SatelliteDish,
  Settings,
  Sun,
} from "lucide-vue-next"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Toaster } from "@/components/ui/sonner"
import { socket } from "@/socket"
import { useAlerts } from "@/lib/alerts"

const route = useRoute()
const THEME_STORAGE_KEY = "skyhook-theme"
const isDark = ref(false)

type NavItem = {
  section: string | null
  title: string
  name: string
  to: string
  icon: Component
}

const items: NavItem[] = [
  { section: null, title: "Overview", name: "Overview", to: "/", icon: LayoutDashboard },
  { section: "Avionics", title: "Data", name: "data", to: "/data", icon: HardDriveDownload },
  { section: "Comms", title: "Communications", name: "comms", to: "/comms", icon: RadioTower },
  { section: "Stations", title: "Ground Station", name: "ground-station", to: "/ground-station", icon: SatelliteDish },
  { section: "Stations", title: "Pad Station", name: "pad-station", to: "/pad-station", icon: ChevronsLeftRightEllipsis },
  { section: "Active flight controls", title: "Engine", name: "engine", to: "/engine", icon: FlameIcon },
  { section: "Active flight controls", title: "Airbrakes", name: "airbrakes", to: "/airbrakes", icon: Settings },
  { section: "Active flight controls", title: "Fins", name: "fins", to: "/fins", icon: GamepadDirectional },
  { section: "Cameras", title: "On-Board", name: "on-board", to: "/on-board", icon: Cctv },
  { section: "Cameras", title: "Ground", name: "ground", to: "/ground-cams", icon: Camera },
]

const grouped = computed(() => {
  const bySection = new Map<NavItem["section"], NavItem[]>()
  const order: Array<NavItem["section"]> = []

  for (const item of items) {
    const key = item.section ?? null
    let group = bySection.get(key)
    if (!group) {
      group = []
      bySection.set(key, group)
      order.push(key)
    }
    group.push(item)
  }

  const orderedKeys: Array<NavItem["section"]> = [
    ...(bySection.has(null) ? [null] : []),
    ...order.filter((key) => key !== null),
  ]

  return orderedKeys.map((section) => ({
    section,
    items: bySection.get(section) ?? [],
  }))
})

const TOTAL_SECONDS = 5 * 60 * 60
const remainingSeconds = ref(TOTAL_SECONDS)

const formatRemainingTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `T-${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`
}

const timer = ref(formatRemainingTime(remainingSeconds.value))

const tickTimer = () => {
  if (remainingSeconds.value > 0) {
    remainingSeconds.value -= 1
  }
  timer.value = formatRemainingTime(remainingSeconds.value)
}

const uplinkSpeed = ref("")
const nbSpeed = ref("")
const bbSpeed = ref("")
const wsStatus = ref(socket.connected ? "Online" : "Offline")
const isOnline = computed(() => wsStatus.value === "Online")
const wsBadgeClass = computed(() => {
  if (wsStatus.value === "Online") {
    return "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
  }
  if (wsStatus.value === "Connecting..." || wsStatus.value === "Reconnecting...") {
    return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
  }
  return "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
})

const formatSpeed = (minKb: number, maxKb: number) =>
  `${(Math.random() * (maxKb - minKb) + minKb).toFixed(1)}kb/s`

const updateMetrics = () => {
  tickTimer()
  uplinkSpeed.value = formatSpeed(30, 140)
  nbSpeed.value = formatSpeed(90, 260)
  bbSpeed.value = `${(Math.random() * 6).toFixed(1)}mb/s`
}

const applyTheme = (dark: boolean) => {
  isDark.value = dark
  const root = document.documentElement
  root.classList.toggle("dark", dark)
  localStorage.setItem(THEME_STORAGE_KEY, dark ? "dark" : "light")
}

const toggleTheme = () => applyTheme(!isDark.value)

let intervalId: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  const storedPreference = localStorage.getItem(THEME_STORAGE_KEY)
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
  applyTheme(storedPreference ? storedPreference === "dark" : prefersDark)
})

onMounted(() => {
  const { show } = useAlerts()
  let hasShownDisconnect = false

  const showDisconnected = () => {
    if (!hasShownDisconnect) {
      show({
        title: "Disconnected from server",
        description: "You have been disconnected from the server. Please check your network connection, and validate that the server is running.",
        variant: "destructive",
      })
      hasShownDisconnect = true
    }
  }

  const showReconnected = () => {
    if (hasShownDisconnect) {
      show({
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

  updateMetrics()
  intervalId = setInterval(updateMetrics, 1000)

  wsStatus.value = socket.connected ? "Online" : "Connecting..."
  socket.on("connect", setOnline)
  socket.on("disconnect", setOffline)
  socket.on("connect_error", setOffline)
  socket.io.on("reconnect_attempt", setReconnecting)
  socket.io.on("reconnect", setOnline)
  socket.io.on("reconnect_error", setOffline)
})

onBeforeUnmount(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
  socket.off("connect")
  socket.off("disconnect")
  socket.off("connect_error")
  socket.io.off("reconnect_attempt")
  socket.io.off("reconnect")
  socket.io.off("reconnect_error")
})
</script>

<template>
  <SidebarProvider class="h-svh">
    <Sidebar variant="inset" collapsible="none">
      <SidebarHeader class="px-2 py-2">
        <div class="px-2 text-sm font-semibold">Skyhook Interface</div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup v-for="group in grouped" :key="group.section ?? '__top__'">
          <SidebarGroupLabel v-if="group.section !== null">
            {{ group.section }}
          </SidebarGroupLabel>

          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem v-for="item in group.items" :key="item.to + ':' + item.title">
                <SidebarMenuButton :is-active="route.name === item.name" as-child>
                  <RouterLink :to="item.to">
                    <component :is="item.icon" />
                    <span>{{ item.title }}</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div class="flex items-center gap-3 border-t border-sidebar-border/60 px-2 py-3">
          <Avatar class="h-10 w-10">
            <AvatarFallback>SK</AvatarFallback>
          </Avatar>
          <div class="min-w-0 text-left">
            <div class="truncate text-sm font-semibold">Skyhook Administrator</div>
            <div class="truncate text-xs text-muted-foreground">username@tu-berlin.de</div>
          </div>
          <div class="ml-auto flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              :aria-pressed="isDark"
              :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
              title="Toggle theme"
              @click="toggleTheme"
            >
              <Sun v-if="isDark" class="h-4 w-4" />
              <Moon v-else class="h-4 w-4" />
            </Button>
            <RouterLink to="/settings">
              <Button variant="ghost" size="icon" aria-label="Settings" title="Settings">
                <Settings class="h-4 w-4" />
              </Button>
            </RouterLink>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>

    <!-- ✅ changed: flex column + header + centered content -->
    <SidebarInset class="min-h-svh pb-12 flex flex-col bg-muted/20">
      <!-- top header bar -->
      <header class="sticky top-0 z-10 border-b bg-background/70 backdrop-blur">
        <div class="mx-auto flex max-w-6xl items-center gap-2 px-4 py-3 md:px-6">
          <div class="text-sm font-semibold">
            {{ String(route.name ?? "Overview") }}
          </div>

          <div class="ml-auto flex items-center gap-2">
            <Badge variant="outline" class="text-xs">{{ timer }}</Badge>
            <Badge variant="outline" class="text-xs" :class="wsBadgeClass">{{ wsStatus }}</Badge>
          </div>
        </div>
      </header>

      <!-- page content wrapper -->
      <main class="flex-1">
        <div class="mx-auto max-w-6xl p-4 md:p-6">
          <RouterView />
        </div>
      </main>
    </SidebarInset>

    <!-- bottom status strip: slightly more “polished” -->
    <div
      class="fixed bottom-0 left-0 right-0 z-20 bg-background/70 backdrop-blur border-t shadow-sm md:left-[var(--sidebar-width)]"
    >
      <div class="mx-auto flex h-[44px] max-w-6xl items-center gap-2 px-2 md:px-6">

        <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
          <ArrowUpFromLine class="h-4 w-4" />
          {{ uplinkSpeed }}
        </Badge>

        <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
          <ArrowDownToLine class="h-4 w-4" />
          {{ nbSpeed }}
        </Badge>

        <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
          <ArrowDownToLine class="h-4 w-4" />
          {{ bbSpeed }}
        </Badge>
      </div>
    </div>

    <Toaster />
  </SidebarProvider>
</template>
