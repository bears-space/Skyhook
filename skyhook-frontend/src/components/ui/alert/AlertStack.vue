<script setup>
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useAlerts } from "@/lib/alerts"
import { AlertTriangle, Info, X } from "lucide-vue-next"

const { alerts, remove } = useAlerts()

const iconFor = (alert) => {
  if (alert.icon) return alert.icon
  return alert.variant === "destructive" ? AlertTriangle : Info
}

const iconClass = (alert) =>
  alert.variant === "destructive" ? "text-destructive" : "text-foreground"
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-end px-4 sm:top-6 sm:px-6">
      <div class="pointer-events-auto w-full max-w-md space-y-2">
        <Alert
          v-for="alert in alerts"
          :key="alert.id"
          :variant="alert.variant"
          class="flex items-start gap-3 pr-3 border border-border/70 bg-background/95 text-foreground shadow-lg backdrop-blur supports-[backdrop-filter]:bg-background/75 dark:bg-background/80 supports-[backdrop-filter]:dark:bg-background/60 [&>svg]:static [&>svg]:mt-1 [&>svg]:shrink-0"
        >
          <component :is="iconFor(alert)" :class="['h-4 w-4', iconClass(alert)]" aria-hidden="true" />
          <div class="flex-1 space-y-1">
            <AlertTitle v-if="alert.title">{{ alert.title }}</AlertTitle>
            <AlertDescription v-if="alert.description">
              {{ alert.description }}
            </AlertDescription>
          </div>
          <button
            type="button"
            class="ml-2 inline-flex h-7 w-7 items-center justify-center rounded-md text-sm text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            aria-label="Dismiss alert"
            @click="remove(alert.id)"
          >
            <X class="h-4 w-4" aria-hidden="true" />
          </button>
        </Alert>
      </div>
    </div>
  </Teleport>
</template>
