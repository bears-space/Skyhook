<script setup lang="ts">
import type { Component } from "vue"
import { computed } from "vue"
import { RouterLink, useRouter } from "vue-router"
import {
  Camera,
  Cctv,
  ChevronsLeftRightEllipsis,
  FlameIcon,
  GamepadDirectional,
  HardDriveDownload,
  LayoutDashboard,
  LogOut,
  Moon,
  RadioTower,
  SatelliteDish,
  Server,
  Settings,
  Sun,
  User,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { useSidebar } from "@/components/ui/sidebar"
import logoDark from "@/assets/maxres_light.png"
import logoLight from "@/assets/maxres_dark.png"

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
  compact: boolean
  showLabels: boolean
  userName?: string | null
  userEmail?: string | null
}>()

const emit = defineEmits<{
  (event: "toggle-theme"): void
  (event: "sign-out"): void
}>()

const router = useRouter()
const { isMobile } = useSidebar()

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

const logoSrc = computed(() => (props.isDark ? logoDark : logoLight))
const showTextLabels = computed(() => props.showLabels || isMobile.value)
const initials = computed(() => {
  const source = props.userName ?? "SK"
  return source
    .trim()
    .split(/\s+/)
    .map((part) => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join("") || "SK"
})
</script>

<template>
  <Sidebar variant="inset" :collapsible="props.showLabels ? 'none' : 'icon'">
    <SidebarHeader :class="cn(props.compact ? 'px-1.5 py-1.5' : 'px-2 py-2')">
      <div :class="cn('flex items-center px-2', showTextLabels ? 'gap-2' : 'justify-center px-0')">
        <img :src="logoSrc" alt="Skyhook logo" :class="cn(props.compact ? 'h-7 w-auto' : 'h-8 w-auto')" />
        <div v-if="showTextLabels" class="text-sm font-semibold">Skyhook Interface</div>
      </div>
    </SidebarHeader>

    <SidebarContent>
      <SidebarGroup v-for="group in grouped" :key="group.section ?? '__top__'">
        <SidebarGroupLabel v-if="group.section !== null && showTextLabels">
          {{ group.section }}
        </SidebarGroupLabel>

        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="item in group.items" :key="item.to + ':' + item.title">
              <SidebarMenuButton
                :is-active="props.currentRouteName === item.name"
                :size="props.compact ? 'sm' : 'default'"
                :tooltip="showTextLabels ? undefined : item.title"
                as-child
              >
                <RouterLink :to="item.to">
                  <component :is="item.icon" />
                  <span v-if="showTextLabels">{{ item.title }}</span>
                </RouterLink>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>

    <SidebarFooter>
      <div
        :class="
          cn(
            'border-t border-sidebar-border/60',
            showTextLabels
              ? props.compact
                ? 'flex items-center gap-2 px-1.5 py-2.5'
                : 'flex items-center gap-3 px-2 py-3'
              : 'flex flex-col items-center gap-2 px-1 py-3',
          )
        "
      >
        <Avatar :class="cn(props.compact ? 'h-9 w-9' : 'h-10 w-10')">
          <AvatarFallback>{{ initials }}</AvatarFallback>
        </Avatar>
        <div v-if="showTextLabels" class="min-w-0 text-left">
          <div class="truncate text-sm font-semibold">{{ props.userName ?? "Skyhook Operator" }}</div>
          <div class="truncate text-xs text-muted-foreground">{{ props.userEmail ?? "operator@skyhook.local" }}</div>
        </div>
        <div :class="cn(showTextLabels ? 'ml-auto flex items-center gap-1' : 'flex flex-col items-center gap-1')">
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
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="ghost" size="icon" aria-label="Settings" title="Settings">
                <Settings class="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" side="top" class="w-48">
              <DropdownMenuLabel>Settings</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="router.push({ path: '/settings/user' })">
                <User class="h-4 w-4 text-muted-foreground" />
                <span>User</span>
              </DropdownMenuItem>
              <DropdownMenuItem @click="router.push({ path: '/settings/system' })">
                <Server class="h-4 w-4 text-muted-foreground" />
                <span>System</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem class="text-destructive" @click="emit('sign-out')">
                <LogOut class="h-4 w-4" />
                <span>Sign out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </SidebarFooter>
  </Sidebar>
</template>
