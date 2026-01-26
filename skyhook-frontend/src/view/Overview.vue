<script setup lang="ts">
import { computed, onMounted, ref, toRef, watchEffect } from "vue"
import Badge from "@/components/ui/badge/Badge.vue"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { storeToRefs } from "pinia"
import { useLaunchpadStore } from "@/stores/launchpad"

const lp = useLaunchpadStore()
const { countdownText, timer, meta } = storeToRefs(lp)

// 1) phase VALUE (what you actually show)
const phase = computed(() => timer.value.phase.value) // "T-" | "T+" | "N/A"

// 2) phase META (age/stale/ts)
const phaseMeta = computed(() => meta.value.timer.phase) // { ts, ageMs, isStale }

// optional: if you want the whole Timed<> field as a ref
const phaseField = toRef(timer.value, "phase") // Ref<Timed<"T-" | "T+" | "N/A">>

type EventRow = {
  time: string
  source: string
  level: "info" | "warn" | "error"
  message: string
}

const mission = ref({
  vehicle: "Aerobär",
  phase: "Pre-flight phase",
  pad: "Pad Station 1",
  wind: "6.2 m/s",
  gps: "52.5123, 13.3267",
})

type KpiTone = "ok" | "warn" | "info" | "error" | "neutral" 

type KpiStatus = {
  tone: KpiTone
  message: string
}

type Kpi = {
  label: string
  value: string
  statuses: KpiStatus[]
}

const kpis = ref<Kpi[]>([
  {
    label: "Launch Timer",
    value: phase.value + "" + countdownText.value,
    statuses: [
      { tone: "ok", message: "Ground has control over timer" },
    ],
  },
  {
    label: "Avionics",
    value: "Armed",
    statuses: [
      { tone: "warn", message: "Awaiting manual arming" }
    ],
  },
  {
    label: "Comms",
    value: "Online",
    statuses: [
      { tone: "ok", message: "Uplink" },
      { tone: "warn", message: "NB" },
      { tone: "ok", message: "BB" },
    ],
  },
  {
    label: "Cameras",
    value: "2/3",
    statuses: [
      { tone: "ok", message: "OB1" },
      { tone: "ok", message: "OB2" },
      { tone: "error", message: "Pad" },
    ],
  },
  {
    label: "Ground Station",
    value: "Operational",
    statuses: [
      { tone: "ok", message: "Wi-Fi link" }
    ],
  },
  {
    label: "Weather",
    value: "NE 6.2 m/s",
    statuses: [
      { tone: "warn", message: "Strong winds" },
      { tone: "neutral", message: "32°C" },
    ],
  },
  {
    label: "Radar",
    value: "Locked-On",
    statuses: [
      { tone: "ok", message: "Mode: IR" },
    ],
  },
])

watchEffect(() => {
  const timerKpi = kpis.value.find(k => k.label === "Launch Timer")
  if (timerKpi) {
    timerKpi.value = `${phase.value}${countdownText.value}`
  }
})

const events = ref<EventRow[]>([
  { time: "T-00:04:21", source: "Pad", level: "info", message: "Hold-down clamps verified." },
  { time: "T-00:04:02", source: "Comms", level: "info", message: "NB uplink stable (avg 180 kb/s)." },
  { time: "T-00:03:37", source: "Avionics", level: "warn", message: "IMU temperature rising (+2.1°C)." },
  { time: "T-00:03:10", source: "Engine", level: "info", message: "Ignition circuit continuity OK." },
  { time: "T-00:02:48", source: "Ground", level: "error", message: "Cam-2 dropped frames (recovering…)" },
])

const badgeForLevel = computed(() => (lvl: EventRow["level"]) => {
  if (lvl === "error") return "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
  if (lvl === "warn") return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
  return "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
})

const badgeForTone = (tone: KpiTone) => {
  if (tone === "ok") return "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
  if (tone === "warn") return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
  if (tone === "info") return "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
  if (tone === "error") return "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
  if (tone === "neutral") return "bg-muted text-muted-foreground"
  return "bg-muted text-muted-foreground"
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <div class="text-lg font-semibold">Overview</div>
        <div class="text-sm text-muted-foreground">
          Live summary + recent events
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <Badge variant="outline">{{ mission.vehicle }}</Badge>
        <Badge variant="outline">{{ mission.phase }}</Badge>
        <Badge variant="outline">{{ mission.pad }}</Badge>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card v-for="k in kpis" :key="k.label" class="shadow-sm">
        <CardHeader class="pb-2">
          <CardDescription>{{ k.label }}</CardDescription>
          <CardTitle class="text-2xl">
            {{ k.value }}
          </CardTitle>
        </CardHeader>
        <CardContent class="pt-0">
          <div class="flex flex-wrap gap-2">
            <Badge
              v-for="status in k.statuses"
              :key="`${k.label}-${status.message}`"
              variant="outline"
              class="text-xs"
              :class="badgeForTone(status.tone)"
            >
              {{ status.message }}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Mission summary + Events -->
    <div class="grid gap-4 lg:grid-cols-3">
      <Card class="lg:col-span-1 shadow-sm">
        <CardHeader>
          <CardTitle>Mission</CardTitle>
          <CardDescription>Current environment + GPS</CardDescription>
        </CardHeader>
        <CardContent class="space-y-2 text-sm">
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">Wind</span><span>{{ mission.wind }}</span></div>
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">GPS</span><span class="font-mono">{{ mission.gps }}</span></div>
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">Phase</span><span>{{ mission.phase }}</span></div>
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">Pad</span><span>{{ mission.pad }}</span></div>
        </CardContent>
      </Card>

      <Card class="lg:col-span-2 shadow-sm">
        <CardHeader>
          <CardTitle>Recent events</CardTitle>
          <CardDescription>Last 5 system messages</CardDescription>
        </CardHeader>

        <CardContent class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-muted-foreground">
              <tr class="border-b">
                <th class="py-2 text-left font-medium">Time</th>
                <th class="py-2 text-left font-medium">Source</th>
                <th class="py-2 text-left font-medium">Level</th>
                <th class="py-2 text-left font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in events" :key="e.time + e.source" class="border-b last:border-b-0">
                <td class="py-2 font-mono text-xs">{{ e.time }}</td>
                <td class="py-2">{{ e.source }}</td>
                <td class="py-2">
                  <Badge variant="outline" class="text-xs" :class="badgeForLevel(e.level)">
                    {{ e.level }}
                  </Badge>
                </td>
                <td class="py-2 text-muted-foreground">{{ e.message }}</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
