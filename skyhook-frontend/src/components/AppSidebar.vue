<script setup>
import { RouterLink, useRoute } from "vue-router"
import { computed } from "vue"
import { Antenna, Camera, Cctv, ChevronsLeftRightEllipsis, Flame, FlameIcon, FlameKindling, FlameKindlingIcon, GamepadDirectional, HardDriveDownload, Home, LayoutDashboard, RadioTower, SatelliteDish, Settings } from "lucide-vue-next"
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
} from "@/components/ui/sidebar"

const route = useRoute()

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
  </Sidebar>
</template>