<script setup lang="ts">
import Badge from "@/components/ui/badge/Badge.vue"
import { storeToRefs } from "pinia"
import { useLaunchpadStore } from "@/stores/launchpad"
import { computed } from "vue"

const lp = useLaunchpadStore()
const { countdownText, timer, launch } = storeToRefs(lp)

const launchHold = computed(() => launch.value.hold.value)

const phaseText = computed(() => timer.value.phase.value + countdownText.value)
const phaseBadgeClass = computed(() => {
  if (launchHold.value) {
    return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
  }
})

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
        <Badge variant="outline" class="text-xs" :class="props.wsBadgeClass">{{ props.wsStatus }}</Badge>
        <Badge variant="outline" class="text-xs" :class="phaseBadgeClass">{{ phaseText }}</Badge>
      </div>
    </div>
  </header>
</template>
