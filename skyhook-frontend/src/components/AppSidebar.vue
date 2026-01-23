<script setup>
import { RouterLink, useRoute } from "vue-router"
import { Home, Settings } from "lucide-vue-next"
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
  { title: "Home", name: "dashboard", to: "/", icon: Home },
  { title: "Settings", name: "settings", to: "/settings", icon: Settings },
]
</script>

<template>
  <Sidebar variant="inset" collapsible="none">
    <SidebarHeader class="px-2 py-2">
      <div class="px-2 text-sm font-semibold">Skyhook Interface</div>
    </SidebarHeader>

    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>App</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="item in items" :key="item.title">
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
