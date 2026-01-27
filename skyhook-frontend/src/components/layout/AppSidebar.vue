<script setup lang="ts">
import type { Component } from "vue"
import { computed } from "vue"
import { RouterLink } from "vue-router"
import {
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
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

type NavItem = {
  section: string | null
  title: string
  name: string
  to: string
  icon: Component
}

const props = defineProps<{
  currentRouteName?: string | null
  isDark: boolean
}>()

const emit = defineEmits<{
  (event: "toggle-theme"): void
}>()

const items: NavItem[] = [
  { section: null, title: "Overview", name: "Overview", to: "/", icon: LayoutDashboard },
  { section: "Avionics Data", title: "Telemetry", name: "telemetry", to: "/telemetry", icon: HardDriveDownload },
  { section: null, title: "System", name: "system", to: "/system", icon: HardDriveDownload },
  { section: "Comms", title: "Narrowband", name: "narrowband", to: "/narrowband", icon: RadioTower },
  { section: "Comms", title: "Broadband", name: "broadband", to: "/broadband", icon: RadioTower },
  { section: "Comms", title: "Wi-Fi Link", name: "wifi-link", to: "/wifi-link", icon: RadioTower },
  { section: "Stations", title: "Ground Station", name: "ground-station", to: "/ground-station", icon: SatelliteDish },
  { section: "Stations", title: "Launch Pad Station", name: "pad-station", to: "/pad-station", icon: ChevronsLeftRightEllipsis },
  { section: "Active flight controls", title: "Engine", name: "engine", to: "/engine", icon: FlameIcon },
  { section: "Active flight controls", title: "Airbrakes", name: "airbrakes", to: "/airbrakes", icon: Settings },
  { section: "Active flight controls", title: "Fins", name: "fins", to: "/fins", icon: GamepadDirectional },
  { section: "Avionics Data", title: "On-Board", name: "on-board", to: "/on-board", icon: Cctv },
  { section: "Avionics Data", title: "Ground", name: "ground", to: "/ground-cams", icon: Camera },
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
</script>

<template>
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
              <SidebarMenuButton :is-active="props.currentRouteName === item.name" as-child>
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
            :aria-pressed="props.isDark"
            :aria-label="props.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
            title="Toggle theme"
            @click="emit('toggle-theme')"
          >
            <Sun v-if="props.isDark" class="h-4 w-4" />
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
