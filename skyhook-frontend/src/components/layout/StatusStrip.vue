<script setup lang="ts">
import Badge from "@/components/ui/badge/Badge.vue"
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-vue-next"

const props = defineProps<{
  uplinkSpeed: string
  nbSpeed: string
  bbSpeed: string
}>()
</script>

<template>
  <div
    class="fixed bottom-0 left-0 right-0 z-20 bg-background/70 backdrop-blur border-t shadow-sm md:left-[var(--sidebar-width)]"
  >
    <div class="mx-auto flex h-[44px] max-w-6xl items-center gap-2 px-2 md:px-6">
      <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowUpFromLine class="h-4 w-4" />
        {{ props.uplinkSpeed }}
      </Badge>

      <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowDownToLine class="h-4 w-4" />
        {{ props.nbSpeed }}
      </Badge>

      <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowDownToLine class="h-4 w-4" />
        {{ props.bbSpeed }}
      </Badge>
    </div>
  </div>
</template>
