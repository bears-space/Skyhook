<script setup lang="ts">
import Badge from "@/components/ui/badge/Badge.vue"
import { storeToRefs } from "pinia"
import { useLaunchpadStore } from "@/stores/launchpad"
import { computed } from "vue"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"
import { ArrowUpFromLine } from "lucide-vue-next"

const lp = useLaunchpadStore()
const { countdownText, timer, launch } = storeToRefs(lp)

const launchHold = computed(() => launch.value.hold.value)

const phaseText = computed(() => {
  if (timer.value.phase.value === "N/A") return "n/a"
  return `${timer.value.phase.value}${countdownText.value}`
})
const phaseBadgeClass = computed(() => {
  if (launchHold.value) {
    return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
  }
})

const props = defineProps<{
  routeName?: string | null
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
        <HoverCard>
          <HoverCardTrigger as-child>
            <Badge variant="outline" class="text-xs" :class="props.wsBadgeClass">{{ props.wsStatus }}</Badge>
          </HoverCardTrigger>
          <HoverCardContent class="w-56">
            <div class="flex items-center gap-2 text-sm font-semibold text-foreground">
              <ArrowUpFromLine class="h-4 w-4 text-green-600 dark:text-green-300" />
              Server connection
            </div>
            <p class="mt-2 text-xs text-muted-foreground">
              Server WebSocket connectivity status.
            </p>
          </HoverCardContent>
        </HoverCard>

        <Badge variant="outline" class="text-xs" :class="phaseBadgeClass">{{ phaseText }}</Badge>
      </div>
    </div>
  </header>
</template>
