<script setup>
import AppSidebar from "@/components/AppSidebar.vue"
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar"
</script>

<template>
  <SidebarProvider class="min-h-screen w-full">
    <div class="flex min-h-screen w-full">
      <AppSidebar class="shrink-0" />

      <SidebarInset class="flex min-h-screen flex-1 flex-col">
        <header class="flex h-16 items-center gap-2 border-b px-4">
          <SidebarTrigger class="md:hidden" />
          <div class="font-semibold">Dashboard</div>
        </header>

        <main class="flex-1 overflow-y-auto p-4">
          <slot />
        </main>
      </SidebarInset>
    </div>
  </SidebarProvider>
</template>
