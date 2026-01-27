<script setup lang="ts">
import Badge from "@/components/ui/badge/Badge.vue"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"
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
      <HoverCard>
        <HoverCardTrigger as-child>
          <Badge
            variant="outline"
            class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
          >
            <ArrowDownToLine class="h-4 w-4" />
            {{ props.uplinkSpeed }}
          </Badge>
        </HoverCardTrigger>
        <HoverCardContent class="w-56">
          <div class="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ArrowUpFromLine class="h-4 w-4 text-green-600 dark:text-green-300" />
            Uplink throughput
          </div>
          <p class="mt-2 text-xs text-muted-foreground">
            Current transmit speed for outbound rocket traffic.
          </p>
        </HoverCardContent>
      </HoverCard>

      <HoverCard>
        <HoverCardTrigger as-child>
          <Badge
            variant="outline"
            class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
          >
            <ArrowDownToLine class="h-4 w-4" />
            {{ props.nbSpeed }}
          </Badge>
        </HoverCardTrigger>
        <HoverCardContent class="w-56">
          <div class="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ArrowDownToLine class="h-4 w-4 text-green-600 dark:text-green-300" />
            Narrowband downlink
          </div>
          <p class="mt-2 text-xs text-muted-foreground">
            Inbound telemetry and control channel speed.
          </p>
        </HoverCardContent>
      </HoverCard>

      <HoverCard>
        <HoverCardTrigger as-child>
          <Badge
            variant="outline"
            class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
          >
            <ArrowDownToLine class="h-4 w-4" />
            {{ props.bbSpeed }}
          </Badge>
        </HoverCardTrigger>
        <HoverCardContent class="w-56">
          <div class="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ArrowDownToLine class="h-4 w-4 text-green-600 dark:text-green-300" />
            Broadband downlink
          </div>
          <p class="mt-2 text-xs text-muted-foreground">
            Payload data rate for high-volume downlink traffic.
          </p>
        </HoverCardContent>
      </HoverCard>
    </div>
  </div>
</template>
