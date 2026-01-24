<script setup>
import AppSidebar from "@/components/AppSidebar.vue"
import StatusBarFooter from "@/components/StatusBarFooter.vue";
import Badge from "@/components/ui/badge/Badge.vue";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar"
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-vue-next";
</script>

<template>
  <SidebarProvider class="min-h-screen w-full">
    <div class="flex min-h-screen w-full">
      <AppSidebar class="shrink-0" />

      <SidebarInset class="flex min-h-screen flex-1 flex-col">
        <main class="flex-1 overflow-y-auto p-4">
          <slot />
        </main>

        <StatusBarFooter />
      </SidebarInset>
    </div>
  </SidebarProvider>
</template>
