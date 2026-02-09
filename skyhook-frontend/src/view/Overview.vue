<script setup lang="ts">
import { computed } from "vue"
import Badge from "@/components/ui/badge/Badge.vue"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { storeToRefs } from "pinia"
import { useLaunchpadStore } from "@/stores/launchpad"
import { useCommsStore } from "@/stores/comms"
import { useTelemetryStore } from "@/stores/telemetry"

const NA = "n/a"
const lp = useLaunchpadStore()
const comms = useCommsStore()
const telemetry = useTelemetryStore()

const { countdownText, timer, launch, weather } = storeToRefs(lp)
const { meta: commsMeta, overallHealth, nb, bb, system } = storeToRefs(comms)

const launchHold = computed(() => launch.value.hold.value)
const launchHoldHasData = computed(() => launch.value.hold.ts > 0)

const launchTimerText = computed(() => {
  if (timer.value.phase.value === "N/A") return NA
  return `${timer.value.phase.value}${countdownText.value}`
})

const windText = computed(() => {
  const w = weather.value.windSpeedMs.value
  const dir = weather.value.windDirDeg.value
  let dirText = ""
  if (dir != null) {
    if (dir >= 337.5 || dir < 22.5) dirText = "N"
    else if (dir >= 22.5 && dir < 67.5) dirText = "NE"
    else if (dir >= 67.5 && dir < 112.5) dirText = "E"
    else if (dir >= 112.5 && dir < 157.5) dirText = "SE"
    else if (dir >= 157.5 && dir < 202.5) dirText = "S"
    else if (dir >= 202.5 && dir < 247.5) dirText = "SW"
    else if (dir >= 247.5 && dir < 292.5) dirText = "W"
    else if (dir >= 292.5 && dir < 337.5) dirText = "NW"
  }
  return w != null && dirText ? `${dirText} ${w.toFixed(1)}m/s` : NA
})

type EventRow = {
  time: string
  source: string
  level: "info" | "warn" | "error"
  message: string
}

const missionVehicle = computed(() => NA)
const missionPad = computed(() => NA)
const missionPhase = computed(() => launchTimerText.value)
const missionWind = computed(() => windText.value)

const gpsFix = computed(() => telemetry.valueByKey<Record<string, unknown>>("gps_fix"))
const gpsText = computed(() => {
  const gps = gpsFix.value as { lat?: number; lon?: number } | null
  if (!gps || typeof gps.lat !== "number" || typeof gps.lon !== "number") return NA
  return `${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)}`
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

const toneForHealth = (h: string): KpiTone => {
  if (h === "ok") return "ok"
  if (h === "degraded") return "warn"
  if (h === "offline") return "error"
  return "neutral"
}

const commsHasData = computed(
  () =>
    commsMeta.value.nb.up.health.ts > 0 ||
    commsMeta.value.nb.down.health.ts > 0 ||
    commsMeta.value.bb.down.health.ts > 0
)
const commsOverallText = computed(() => (commsHasData.value ? overallHealth.value : NA))
const nbUpHealthText = computed(() =>
  commsMeta.value.nb.up.health.ts > 0 ? nb.value.up.health.value : NA
)
const nbDownHealthText = computed(() =>
  commsMeta.value.nb.down.health.ts > 0 ? nb.value.down.health.value : NA
)
const bbDownHealthText = computed(() =>
  commsMeta.value.bb.down.health.ts > 0 ? bb.value.down.health.value : NA
)

const armedValue = computed(() => telemetry.valueByKey<number>("armed"))
const statusValue = computed(() => telemetry.valueByKey<string>("status"))
const batteryValue = computed(() => telemetry.valueByKey<number>("battery_v"))

const avionicsValue = computed(() => {
  if (armedValue.value == null) return NA
  return armedValue.value ? "Armed" : "Disarmed"
})

const avionicsStatuses = computed<KpiStatus[]>(() => {
  const out: KpiStatus[] = []
  out.push({
    tone: statusValue.value ? "info" : "neutral",
    message: statusValue.value ? `Status: ${statusValue.value}` : "Status: n/a",
  })
  out.push({
    tone: batteryValue.value != null ? "neutral" : "neutral",
    message: batteryValue.value != null ? `Batt: ${batteryValue.value.toFixed(2)}V` : "Batt: n/a",
  })
  return out
})

const weatherTempText = computed(() => {
  const temp = weather.value.temperatureC.value
  return temp == null ? NA : `${temp.toFixed(1)}°C`
})
const weatherConditionText = computed(() => {
  const cond = weather.value.condition.value
  return cond == null || cond === "" ? NA : cond
})

const groundStationValue = computed(() =>
  system.value.source.ts > 0 && system.value.source.value ? system.value.source.value : NA
)
const groundStationStatus = computed(() =>
  system.value.notes.ts > 0 && system.value.notes.value ? system.value.notes.value : NA
)

const kpis = computed<Kpi[]>(() => ([
  {
    label: "Launch Timer",
    value: launchTimerText.value,
    statuses: [
      {
        tone: launchHoldHasData.value ? (launchHold.value ? "warn" : "ok") : "neutral",
        message: launchHoldHasData.value ? (launchHold.value ? "Launch Hold" : "Go for Launch") : NA,
      },
    ],
  },
  {
    label: "Avionics",
    value: avionicsValue.value,
    statuses: avionicsStatuses.value,
  },
  {
    label: "Comms",
    value: commsOverallText.value,
    statuses: [
      { tone: toneForHealth(nbUpHealthText.value), message: `Uplink: ${nbUpHealthText.value}` },
      { tone: toneForHealth(nbDownHealthText.value), message: `NB: ${nbDownHealthText.value}` },
      { tone: toneForHealth(bbDownHealthText.value), message: `BB: ${bbDownHealthText.value}` },
    ],
  },
  {
    label: "Cameras",
    value: NA,
    statuses: [
      { tone: "neutral", message: NA },
    ],
  },
  {
    label: "Ground Station",
    value: groundStationValue.value,
    statuses: [
      { tone: groundStationStatus.value === NA ? "neutral" : "info", message: groundStationStatus.value },
    ],
  },
  {
    label: "Weather",
    value: windText.value,
    statuses: [
      { tone: weatherConditionText.value === NA ? "neutral" : "info", message: weatherConditionText.value },
      { tone: weatherTempText.value === NA ? "neutral" : "neutral", message: weatherTempText.value },
    ],
  },
  {
    label: "Radar",
    value: NA,
    statuses: [
      { tone: "neutral", message: NA },
    ],
  },
]))

const fmtTime = (ts: number | null | undefined): string => {
  if (!ts) return NA
  return new Date(ts).toLocaleTimeString()
}
const fmtTimeStr = (ts: string | null | undefined): string => {
  if (!ts) return NA
  const parsed = Date.parse(ts)
  if (Number.isNaN(parsed)) return NA
  return new Date(parsed).toLocaleTimeString()
}

const statusItem = computed(() => telemetry.latestByKey("status"))

const events = computed<EventRow[]>(() => {
  const rows: EventRow[] = []

  if (launch.value.hold.ts > 0) {
    rows.push({
      time: fmtTime(launch.value.hold.ts),
      source: "Launch",
      level: launch.value.hold.value ? "warn" : "info",
      message: launch.value.hold.value
        ? `Hold: ${launch.value.holdReason.value || "Hold"}`
        : "Hold released",
    })
  }

  if (statusItem.value?.value) {
    rows.push({
      time: fmtTimeStr(statusItem.value.ts),
      source: "Avionics",
      level: "info",
      message: String(statusItem.value.value),
    })
  }

  if (system.value.notes.ts > 0 && system.value.notes.value) {
    rows.push({
      time: fmtTime(system.value.notes.ts),
      source: "Comms",
      level: "info",
      message: system.value.notes.value,
    })
  }

  if (rows.length === 0) {
    return [{ time: NA, source: NA, level: "info", message: NA }]
  }
  return rows.slice(0, 5)
})

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
        <Badge variant="outline">{{ missionVehicle }}</Badge>
        <Badge variant="outline">{{ missionPhase }}</Badge>
        <Badge variant="outline">{{ missionPad }}</Badge>
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
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">Wind</span><span>{{ missionWind }}</span></div>
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">GPS</span><span class="font-mono">{{ gpsText }}</span></div>
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">Phase</span><span>{{ missionPhase }}</span></div>
          <div class="flex justify-between gap-3"><span class="text-muted-foreground">Pad</span><span>{{ missionPad }}</span></div>
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
