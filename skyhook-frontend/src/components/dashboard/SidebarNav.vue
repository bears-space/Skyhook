<script setup>
import { computed } from "vue"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"

const props = defineProps({
  collapsed: { type: Boolean, default: false },
})

const items = [
  { label: "Overview", href: "#", icon: "🏠" },
  { label: "Devices", href: "#", icon: "🧩" },
  { label: "Logs", href: "#", icon: "📜" },
  { label: "Settings", href: "#", icon: "⚙️" },
]

const labelClass = computed(() => (props.collapsed ? "hidden" : "inline"))
</script>

<template>
  <ScrollArea class="h-full">
    <nav class="p-2 space-y-1">
      <Button
        v-for="it in items"
        :key="it.label"
        variant="ghost"
        class="w-full justify-start gap-3"
        :title="it.label"
      >
        <span class="text-lg">{{ it.icon }}</span>
        <span :class="labelClass">{{ it.label }}</span>
      </Button>
    </nav>
  </ScrollArea>
</template>
