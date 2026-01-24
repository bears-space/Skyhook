<script setup>
import { RouterLink, useRoute } from "vue-router"
import { computed, onMounted, ref } from "vue"
import { Antenna, Camera, Cctv, ChevronsLeftRightEllipsis, Flame, FlameIcon, FlameKindling, FlameKindlingIcon, GamepadDirectional, HardDriveDownload, Home, LayoutDashboard, Moon, RadioTower, SatelliteDish, Settings, Sun } from "lucide-vue-next"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarRail,
  SidebarFooter,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const route = useRoute()
const THEME_STORAGE_KEY = "skyhook-theme"
const isDark = ref(false)

const items = [
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
  const bySection = new Map()
  const order = []

  for (const item of items) {
    const key = item.section ?? null
    if (!bySection.has(key)) {
      bySection.set(key, [])
      order.push(key)
    }
    bySection.get(key).push(item)
  }

  // Ensure null is first
  const orderedKeys = [
    ...(bySection.has(null) ? [null] : []),
    ...order.filter((k) => k !== null),
  ]

  return orderedKeys.map((section) => ({
    section,
    items: bySection.get(section) ?? [],
  }))
})

const applyTheme = (dark) => {
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
</script>

<template>
  <Sidebar variant="inset" collapsible="none">
    <SidebarHeader class="px-2 py-2">
      <div class="px-2 text-sm font-semibold">Skyhook Interface</div>
    </SidebarHeader>

    <SidebarContent>
      <SidebarGroup v-for="group in grouped" :key="group.section ?? '__top__'">
        <!-- Only show label when section is not null -->
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
      <div class="flex items-center gap-3 px-2 py-3 border-t border-sidebar-border/60">
        <Avatar class="h-10 w-10">
          <AvatarFallback>SK</AvatarFallback>
        </Avatar>
        <div class="min-w-0 text-left">
          <div class="truncate text-sm font-semibold">Skyhook Administrator</div>
          <div class="truncate text-xs text-muted-foreground">
            username@tu-berlin.de
          </div>
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
</template>
