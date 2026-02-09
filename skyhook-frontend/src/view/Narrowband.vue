<script setup lang="ts">
import GradientLineApex from "@/components/GradientLineApex.vue"
import Badge from "@/components/ui/badge/Badge.vue"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useCommsStore, type LinkHealth, type LinkState, type TimedMeta } from "@/stores/comms"
import { computed, ref, watch } from "vue"
import { storeToRefs } from "pinia"

type Tone = "ok" | "warn" | "error" | "info" | "neutral"

const NA = "n/a"
const comms = useCommsStore()
const { nb, system, meta, overallHealth } = storeToRefs(comms)

const toneClass = (tone: Tone) => {
  if (tone === "ok") return "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-200"
  if (tone === "warn") return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-200"
  if (tone === "error") return "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-200"
  if (tone === "info") return "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200"
  return "bg-muted text-muted-foreground"
}

const healthTone = (h: LinkHealth | string | undefined): Tone => {
  if (h === NA) return "neutral"
  if (h === "ok") return "ok"
  if (h === "degraded") return "warn"
  if (h === "offline") return "error"
  return "neutral"
}

const stateTone = (s: LinkState | string | undefined): Tone => {
  if (s === NA) return "neutral"
  if (s === "error") return "error"
  if (s === "acquiring") return "warn"
  if (s === "locked" || s === "tx" || s === "rx") return "ok"
  if (s === "idle") return "info"
  return "neutral"
}

const hasData = (m?: TimedMeta): boolean => !!m && m.ts > 0
const staleTone = (m?: TimedMeta): Tone => (hasData(m) ? (m?.isStale ? "warn" : "ok") : "neutral")

const fmtAge = (m?: TimedMeta): string => {
  if (!m || m.ageMs == null) return NA
  if (m.ageMs < 1_000) return "just now"
  if (m.ageMs < 60_000) return `${Math.floor(m.ageMs / 1_000)}s ago`
  const mins = Math.floor(m.ageMs / 60_000)
  if (mins < 120) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  return `${hours}h ago`
}

const liveLabel = (m?: TimedMeta): string => (hasData(m) ? `live · ${fmtAge(m)}` : NA)
const lastUpdateLabel = (m?: TimedMeta): string =>
  hasData(m) ? `Last update ${fmtAge(m)}` : NA
const updateLabel = (m?: TimedMeta): string => (hasData(m) ? `Updated ${fmtAge(m)}` : NA)
const dataStateLabel = (m?: TimedMeta): string =>
  hasData(m) ? (m?.isStale ? "stale" : "live") : NA

const fmtBps = (bps: number | null): string => {
  if (bps == null) return NA
  if (Math.abs(bps) >= 1_000_000) return `${(bps / 1_000_000).toFixed(2)} Mb/s`
  if (Math.abs(bps) >= 1_000) return `${(bps / 1_000).toFixed(1)} kb/s`
  return `${bps.toFixed(0)} b/s`
}
const fmtPct = (n: number | null, digits = 0): string => (n == null ? NA : `${n.toFixed(digits)}%`)
const fmtDb = (n: number | null, unit = "dB"): string => (n == null ? NA : `${n.toFixed(1)} ${unit}`)
const fmtMs = (n: number | null): string => (n == null ? NA : `${n.toFixed(0)} ms`)
const fmtHz = (n: number | null): string => {
  if (n == null) return NA
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(3)} MHz`
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)} kHz`
  return `${n.toFixed(0)} Hz`
}
const fmtTime = (ts: number | null): string => (ts ? new Date(ts).toLocaleTimeString() : NA)
const fmtSci = (n: number | null): string => {
  if (n == null) return NA
  if (n === 0) return "0"
  return n < 0.001 ? n.toExponential(1) : n.toFixed(3)
}

const stateLabel = (s: LinkState | string | undefined): string => {
  if (!s || s === NA) return NA
  if (s === "tx") return "Transmitting"
  if (s === "rx") return "Receiving"
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const MAX_POINTS = 24
const uplinkKbps = ref<Array<number | null>>([])
const downlinkKbps = ref<Array<number | null>>([])
const uplinkCategories = ref<string[]>([])
const downlinkCategories = ref<string[]>([])

const addSample = (
  seriesRef: typeof uplinkKbps,
  catRef: typeof uplinkCategories,
  bps: number | null | undefined,
  ts: number | null | undefined,
) => {
  const scaled = typeof bps === "number" ? Number((bps / 1_000).toFixed(2)) : null
  const label = ts
    ? new Date(ts).toLocaleTimeString("en-US", { minute: "2-digit", second: "2-digit" })
    : NA
  seriesRef.value = [...seriesRef.value, scaled].slice(-MAX_POINTS)
  catRef.value = [...catRef.value, label].slice(-MAX_POINTS)
}

watch(
  () => [nb.value.up.rateBps.ts, nb.value.up.rateBps.value],
  ([ts, val]) => addSample(uplinkKbps, uplinkCategories, val, ts),
  { immediate: true },
)

watch(
  () => [nb.value.down.rateBps.ts, nb.value.down.rateBps.value],
  ([ts, val]) => addSample(downlinkKbps, downlinkCategories, val, ts),
  { immediate: true },
)

const uplinkSeries = computed(() => [
  { name: "Uplink", type: "area", data: uplinkKbps.value },
  { name: "Uplink", type: "line", data: uplinkKbps.value },
])
const downlinkSeries = computed(() => [
  { name: "Downlink", type: "area", data: downlinkKbps.value },
  { name: "Downlink", type: "line", data: downlinkKbps.value },
])
const formatKbpsTick = (val: number | null | undefined) =>
  val == null || Number.isNaN(val) ? NA : `${Number(val).toFixed(1)} kb/s`

type Metric = {
  key: string
  label: string
  value: string
  meta?: TimedMeta
  hint?: string
}

const uplinkMetrics = computed<Metric[]>(() => {
  const m = meta.value.nb.up
  const f = nb.value.up
  return [
    { key: "avg", label: "Avg (10s)", value: fmtBps(f.rateAvgBps.value), meta: m.rateAvgBps },
    { key: "util", label: "Utilization", value: fmtPct(f.utilPct.value, 0), meta: m.utilPct },
    { key: "rssi", label: "RSSI", value: fmtDb(f.rssiDbm.value, "dBm"), meta: m.rssiDbm },
    { key: "snr", label: "SNR", value: fmtDb(f.snrDb.value, "dB"), meta: m.snrDb },
    { key: "ber", label: "BER", value: fmtSci(f.ber.value), meta: m.ber },
    { key: "per", label: "PER", value: fmtPct(f.per.value, 2), meta: m.per },
    { key: "loss", label: "Pkt loss", value: fmtPct(f.packetLossPct.value, 1), meta: m.packetLossPct },
    { key: "latency", label: "Latency", value: fmtMs(f.latencyMs.value), meta: m.latencyMs },
    { key: "jitter", label: "Jitter", value: fmtMs(f.jitterMs.value), meta: m.jitterMs },
    { key: "freq", label: "Center freq", value: fmtHz(f.freqHz.value), meta: m.freqHz },
    { key: "bandwidth", label: "Bandwidth", value: fmtHz(f.bandwidthHz.value), meta: m.bandwidthHz },
    { key: "modcod", label: "Mod/Cod", value: f.modcod.value ?? NA, meta: m.modcod },
    { key: "last-tx", label: "Last Tx", value: fmtTime(f.lastTxEpochMs.value), meta: m.lastTxEpochMs },
    { key: "last-rx", label: "Last Rx", value: fmtTime(f.lastRxEpochMs.value), meta: m.lastRxEpochMs },
  ]
})

const downlinkMetrics = computed<Metric[]>(() => {
  const m = meta.value.nb.down
  const f = nb.value.down
  return [
    { key: "avg", label: "Avg (10s)", value: fmtBps(f.rateAvgBps.value), meta: m.rateAvgBps },
    { key: "util", label: "Utilization", value: fmtPct(f.utilPct.value, 0), meta: m.utilPct },
    { key: "rsrp", label: "RSRP", value: fmtDb(f.rsrpDbm.value, "dBm"), meta: m.rsrpDbm },
    { key: "rsrq", label: "RSRQ", value: fmtDb(f.rsrqDb.value, "dB"), meta: m.rsrqDb },
    { key: "sinr", label: "SINR", value: fmtDb(f.sinrDb.value, "dB"), meta: m.sinrDb },
    { key: "rssi", label: "RSSI", value: fmtDb(f.rssiDbm.value, "dBm"), meta: m.rssiDbm },
    { key: "snr", label: "SNR", value: fmtDb(f.snrDb.value, "dB"), meta: m.snrDb },
    { key: "per", label: "PER", value: fmtPct(f.per.value, 2), meta: m.per },
    { key: "loss", label: "Pkt loss", value: fmtPct(f.packetLossPct.value, 1), meta: m.packetLossPct },
    { key: "latency", label: "Latency", value: fmtMs(f.latencyMs.value), meta: m.latencyMs },
    { key: "jitter", label: "Jitter", value: fmtMs(f.jitterMs.value), meta: m.jitterMs },
    { key: "freq", label: "Center freq", value: fmtHz(f.freqHz.value), meta: m.freqHz },
    { key: "bandwidth", label: "Bandwidth", value: fmtHz(f.bandwidthHz.value), meta: m.bandwidthHz },
    { key: "modcod", label: "Mod/Cod", value: f.modcod.value ?? NA, meta: m.modcod },
    { key: "last-tx", label: "Last Tx", value: fmtTime(f.lastTxEpochMs.value), meta: m.lastTxEpochMs },
    { key: "last-rx", label: "Last Rx", value: fmtTime(f.lastRxEpochMs.value), meta: m.lastRxEpochMs },
  ]
})

const lastUpdateMeta = computed(() => meta.value.system.lastUpdateEpochMs)
const systemSource = computed(() =>
  system.value.source.ts > 0 && system.value.source.value ? system.value.source.value : NA
)

const overallHealthText = computed(() =>
  hasData(meta.value.nb.up.health) ||
  hasData(meta.value.nb.down.health) ||
  hasData(meta.value.bb.down.health)
    ? overallHealth.value
    : NA
)
const nbUpHealthText = computed(() => (hasData(meta.value.nb.up.health) ? nb.value.up.health.value : NA))
const nbDownHealthText = computed(() =>
  hasData(meta.value.nb.down.health) ? nb.value.down.health.value : NA
)
const nbUpStateText = computed(() => (hasData(meta.value.nb.up.state) ? nb.value.up.state.value : NA))
const nbDownStateText = computed(() =>
  hasData(meta.value.nb.down.state) ? nb.value.down.state.value : NA
)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <div class="text-lg font-semibold">Narrowband</div>
        <div class="text-sm text-muted-foreground">
          Live link health for the narrowband command/telemetry channel.
          <span class="font-medium text-foreground">
            Updated {{ hasData(lastUpdateMeta) ? fmtAge(lastUpdateMeta) : NA }} ({{ systemSource }}).
          </span>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <Badge variant="outline" :class="toneClass(healthTone(overallHealthText))">Overall {{ overallHealthText }}</Badge>
        <Badge variant="outline" :class="toneClass(healthTone(nbUpHealthText))">Uplink: {{ nbUpHealthText }}</Badge>
        <Badge variant="outline" :class="toneClass(healthTone(nbDownHealthText))">Downlink: {{ nbDownHealthText }}</Badge>
        <Badge variant="outline" :class="toneClass(staleTone(lastUpdateMeta))">
          {{ lastUpdateLabel(lastUpdateMeta) }}
        </Badge>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <Card class="shadow-sm">
        <CardHeader class="pb-2 space-y-1">
          <CardTitle class="flex flex-wrap items-center gap-2">
            Uplink (Ground → Vehicle)
            <Badge variant="outline" :class="toneClass(healthTone(nbUpHealthText))">
              {{ nbUpHealthText }}
            </Badge>
            <Badge variant="outline" :class="toneClass(stateTone(nbUpStateText))">
              {{ stateLabel(nbUpStateText) }}
            </Badge>
          </CardTitle>
          <CardDescription>Command uplink, narrowband radio.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex flex-wrap items-center gap-3">
            <div class="text-3xl font-semibold leading-tight">
              {{ fmtBps(nb.up.rateBps.value) }}
            </div>
            <Badge variant="outline" :class="toneClass(staleTone(meta.nb.up.rateBps))">
              {{ liveLabel(meta.nb.up.rateBps) }}
            </Badge>
            <Badge variant="outline" class="bg-secondary/60 text-foreground">
              Avg {{ fmtBps(nb.up.rateAvgBps.value) }}
            </Badge>
            <Badge variant="outline" class="bg-secondary/60 text-foreground">
              Util {{ fmtPct(nb.up.utilPct.value, 0) }}
            </Badge>
          </div>

          <GradientLineApex
            title="Throughput (kb/s)"
            :series="uplinkSeries"
            :categories="uplinkCategories"
            :y-label-formatter="formatKbpsTick"
          >
            <Badge class="mt-2" :class="toneClass(staleTone(meta.nb.up.rateBps))">
              {{ lastUpdateLabel(meta.nb.up.rateBps) }}
            </Badge>
          </GradientLineApex>

          <div class="grid gap-3 sm:grid-cols-2">
            <div
              v-for="m in uplinkMetrics"
              :key="`up-${m.key}`"
              class="rounded-lg border bg-card/60 p-3"
            >
              <div class="flex items-center justify-between text-xs text-muted-foreground">
                <span>{{ m.label }}</span>
                <span :class="toneClass(staleTone(m.meta))" class="rounded px-2 py-0.5">
                  {{ dataStateLabel(m.meta) }}
                </span>
              </div>
              <div class="mt-1 text-lg font-semibold leading-tight">
                {{ m.value }}
              </div>
              <div class="text-[11px] text-muted-foreground">
                {{ updateLabel(m.meta) }}
              </div>
              <div v-if="m.hint" class="text-[11px] text-muted-foreground">{{ m.hint }}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card class="shadow-sm">
        <CardHeader class="pb-2 space-y-1">
          <CardTitle class="flex flex-wrap items-center gap-2">
            Downlink (Vehicle → Ground)
            <Badge variant="outline" :class="toneClass(healthTone(nbDownHealthText))">
              {{ nbDownHealthText }}
            </Badge>
            <Badge variant="outline" :class="toneClass(stateTone(nbDownStateText))">
              {{ stateLabel(nbDownStateText) }}
            </Badge>
          </CardTitle>
          <CardDescription>Telemetry return path.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex flex-wrap items-center gap-3">
            <div class="text-3xl font-semibold leading-tight">
              {{ fmtBps(nb.down.rateBps.value) }}
            </div>
            <Badge variant="outline" :class="toneClass(staleTone(meta.nb.down.rateBps))">
              {{ liveLabel(meta.nb.down.rateBps) }}
            </Badge>
            <Badge variant="outline" class="bg-secondary/60 text-foreground">
              Avg {{ fmtBps(nb.down.rateAvgBps.value) }}
            </Badge>
            <Badge variant="outline" class="bg-secondary/60 text-foreground">
              Util {{ fmtPct(nb.down.utilPct.value, 0) }}
            </Badge>
          </div>

          <GradientLineApex
            title="Throughput (kb/s)"
            :series="downlinkSeries"
            :categories="downlinkCategories"
            :y-label-formatter="formatKbpsTick"
          >
            <Badge class="mt-2" :class="toneClass(staleTone(meta.nb.down.rateBps))">
              {{ lastUpdateLabel(meta.nb.down.rateBps) }}
            </Badge>
          </GradientLineApex>

          <div class="grid gap-3 sm:grid-cols-2">
            <div
              v-for="m in downlinkMetrics"
              :key="`down-${m.key}`"
              class="rounded-lg border bg-card/60 p-3"
            >
              <div class="flex items-center justify-between text-xs text-muted-foreground">
                <span>{{ m.label }}</span>
                <span :class="toneClass(staleTone(m.meta))" class="rounded px-2 py-0.5">
                  {{ dataStateLabel(m.meta) }}
                </span>
              </div>
              <div class="mt-1 text-lg font-semibold leading-tight">
                {{ m.value }}
              </div>
              <div class="text-[11px] text-muted-foreground">
                {{ updateLabel(m.meta) }}
              </div>
              <div v-if="m.hint" class="text-[11px] text-muted-foreground">{{ m.hint }}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
