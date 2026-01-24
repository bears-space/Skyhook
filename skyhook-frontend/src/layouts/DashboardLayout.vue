<script setup>
import AppSidebar from "@/components/AppSidebar.vue"
import Badge from "@/components/ui/badge/Badge.vue";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar"
</script>

<template>
  <SidebarProvider class="min-h-screen w-full">
    <div class="flex min-h-screen w-full">
      <AppSidebar class="shrink-0" />

      <SidebarInset class="flex min-h-screen flex-1 flex-col">
        <main class="flex-1 overflow-y-auto p-4">
          <slot />
        </main>

        <div class="h-[40px] shrink-0 flex items-center border-t gap-2 px-2">
          <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
            WebSocket
          </Badge>
          <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
            Uplink
          </Badge>
          <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
            Downlink
          </Badge>
        </div>
      </SidebarInset>
    </div>
  </SidebarProvider>
</template>
