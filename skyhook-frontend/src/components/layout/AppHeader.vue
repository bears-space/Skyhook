<script setup lang="ts">
import Badge from "@/components/ui/badge/Badge.vue"

const props = defineProps<{
  routeName?: string | null
  timer: string
  wsStatus: string
  wsBadgeClass: string
}>()
</script>

<template>
  <header class="sticky top-0 z-10 border-b bg-background/70 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center gap-2 px-4 py-3 md:px-6">
      <div class="text-sm font-semibold">
        {{ String(props.routeName ?? "Overview") }}
      </div>

      <div class="ml-auto flex items-center gap-2">
        <Badge variant="outline" class="text-xs">{{ props.timer }}</Badge>
        <Badge variant="outline" class="text-xs" :class="props.wsBadgeClass">{{ props.wsStatus }}</Badge>
      </div>
    </div>
  </header>
</template>
