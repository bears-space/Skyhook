// src/stores/launchpad.ts
import { defineStore } from "pinia"
import { computed, ref, type Ref } from "vue"

export type TsMs = number
export type Timed<T> = { value: T; ts: TsMs }
export type StoreHealth = "ok" | "degraded" | "offline"

export type TimedMeta = { ts: TsMs; ageMs: number | null; isStale: boolean }

const now = (): TsMs => Date.now()
const field = <T>(initialValue: T, ts: TsMs = 0): Timed<T> => ({ value: initialValue, ts })

export type WeatherState = {
  temperatureC: Timed<number | null>
  humidityPct: Timed<number | null>
  pressureHpa: Timed<number | null>
  windSpeedMs: Timed<number | null>
  windGustMs: Timed<number | null>
  windDirDeg: Timed<number | null>
  precipitationMm: Timed<number | null>
  cloudCoverPct: Timed<number | null>
  visibilityM: Timed<number | null>
  lightningRisk: Timed<boolean | number | null>
  condition: Timed<string | null>
}

export type LaunchState = {
  t0EpochMs: Timed<TsMs | null>
  hold: Timed<boolean>
  holdReason: Timed<string | null>
  lastUpdate: Timed<TsMs | null>
}

export type StatusState = {
  lastFetchTs: Timed<TsMs | null>
  source: Timed<string | null>
  health: Timed<StoreHealth>
}

// ✅ Timed countdown variables (simulated)
export type TimerState = {
  nowEpochMs: Timed<TsMs>
  countdownMs: Timed<number | null>
  countdownText: Timed<string>
  phase: Timed<"T-" | "T+" | "N/A">
}

type WeatherKey = keyof WeatherState
type LaunchKey = keyof LaunchState
type StatusKey = keyof StatusState
type TimerKey = keyof TimerState

type StalePolicy = {
  weather: Record<WeatherKey, number>
  launch: Record<LaunchKey, number>
  status: Record<StatusKey, number>
  timer: Record<TimerKey, number>
}

function setField<
  TObj extends Record<string, Timed<any>>,
  K extends keyof TObj
>(obj: TObj, key: K, value: TObj[K]["value"], ts: TsMs = now()): void {
  obj[key] = { value, ts } as TObj[K]
}

// Handles strict/noUncheckedIndexedAccess by allowing undefined and marking it stale.
function metaFor<T>(f: Timed<T> | undefined, maxAgeMs: number): TimedMeta {
  if (!f) return { ts: 0, ageMs: null, isStale: true }
  const age = f.ts ? now() - f.ts : null
  const stale = age === null ? true : age > maxAgeMs
  return { ts: f.ts, ageMs: age, isStale: stale }
}

function buildMeta<TState extends Record<string, Timed<any>>>(
  stateObj: TState,
  policyObj: Record<keyof TState, number>
): { [K in keyof TState]: TimedMeta } {
  const out = {} as { [K in keyof TState]: TimedMeta }
  for (const k of Object.keys(stateObj) as Array<keyof TState>) {
    out[k] = metaFor(stateObj[k], policyObj[k])
  }
  return out
}

function formatCountdown(ms: number | null): string {
  if (ms === null) return "--:--:--"
  const sign = ms < 0 ? "-" : ""
  const abs = Math.abs(ms)

  const hours = Math.floor(abs / 3_600_000)
  const minutes = Math.floor((abs % 3_600_000) / 60_000)
  const seconds = Math.floor((abs % 60_000) / 1_000)

  const pad2 = (n: number) => String(n).padStart(2, "0")
  return `${sign}${pad2(hours)}:${pad2(minutes)}:${pad2(seconds)}`
}

export const useLaunchpadStore = defineStore("launchpad", () => {
  // ---- state ----
  const weather: Ref<WeatherState> = ref({
    temperatureC: field<number | null>(null),
    humidityPct: field<number | null>(null),
    pressureHpa: field<number | null>(null),
    windSpeedMs: field<number | null>(null),
    windGustMs: field<number | null>(null),
    windDirDeg: field<number | null>(null),
    precipitationMm: field<number | null>(null),
    cloudCoverPct: field<number | null>(null),
    visibilityM: field<number | null>(null),
    lightningRisk: field<boolean | number | null>(null),
    condition: field<string | null>(null),
  })

  const launch: Ref<LaunchState> = ref({
    t0EpochMs: field<TsMs | null>(null),
    hold: field<boolean>(false),
    holdReason: field<string | null>(null),
    lastUpdate: field<TsMs | null>(null),
  })

  const status: Ref<StatusState> = ref({
    lastFetchTs: field<TsMs | null>(null),
    source: field<string | null>(null),
    health: field<StoreHealth>("ok"),
  })

  // ✅ timed countdown variables live here
  const timer: Ref<TimerState> = ref({
    nowEpochMs: field<TsMs>(now()),
    countdownMs: field<number | null>(null),
    countdownText: field<string>("--:--:--"),
    phase: field<"T-" | "T+" | "N/A">("N/A"),
  })

  // ---- per-field stale thresholds ----
  const staleAfterMs = ref<StalePolicy>({
    weather: {
      temperatureC: 10_000,
      humidityPct: 10_000,
      pressureHpa: 20_000,
      windSpeedMs: 5_000,
      windGustMs: 5_000,
      windDirDeg: 10_000,
      precipitationMm: 30_000,
      cloudCoverPct: 30_000,
      visibilityM: 30_000,
      lightningRisk: 5_000,
      condition: 30_000,
    },
    launch: {
      t0EpochMs: 60_000,
      hold: 60_000,
      holdReason: 60_000,
      lastUpdate: 60_000,
    },
    status: {
      lastFetchTs: 30_000,
      source: 5 * 60_000,
      health: 30_000,
    },
    timer: {
      nowEpochMs: 2_000,
      countdownMs: 2_000,
      countdownText: 2_000,
      phase: 2_000,
    },
  })

  // ---- per-field meta (age + stale for EVERY variable) ----
  const meta = computed(() => ({
    weather: buildMeta(weather.value, staleAfterMs.value.weather),
    launch: buildMeta(launch.value, staleAfterMs.value.launch),
    status: buildMeta(status.value, staleAfterMs.value.status),
    timer: buildMeta(timer.value, staleAfterMs.value.timer),
  }))

  // ---- generic helpers (optional) ----
  const ageMs = <T>(f: Timed<T>): number | null => (f.ts ? now() - f.ts : null)
  const isStale = <T>(f: Timed<T>, maxAgeMs: number): boolean => {
    const a = ageMs(f)
    return a === null ? true : a > maxAgeMs
  }

  // ---- actions (setters) ----
  function setWeatherField<K extends WeatherKey>(
    key: K,
    value: WeatherState[K]["value"],
    ts: TsMs = now()
  ): void {
    setField(weather.value, key, value, ts)
  }

  function setT0(epochMs: TsMs | null, ts: TsMs = now()): void {
    setField(launch.value, "t0EpochMs", epochMs, ts)
    setField(launch.value, "lastUpdate", ts, ts)
  }

  function setHold(isHold: boolean, reason: string | null = null, ts: TsMs = now()): void {
    setField(launch.value, "hold", !!isHold, ts)
    setField(launch.value, "holdReason", reason, ts)
    setField(launch.value, "lastUpdate", ts, ts)
  }

  function markStatus(
    patch: { source?: string | null; health?: StoreHealth } = {},
    ts: TsMs = now()
  ): void {
    if ("source" in patch) setField(status.value, "source", patch.source ?? null, ts)
    if ("health" in patch) setField(status.value, "health", patch.health ?? "ok", ts)
    setField(status.value, "lastFetchTs", ts, ts)
  }

  function setStaleAfter(
    group: keyof StalePolicy,
    key: WeatherKey | LaunchKey | StatusKey | TimerKey,
    maxAgeMs: number
  ): void {
    ;(staleAfterMs.value[group] as any)[key] = maxAgeMs
  }

  // ✅ updates the timed countdown fields
  function updateTimer(ts: TsMs = now()): void {
    setField(timer.value, "nowEpochMs", ts, ts)

    const t0 = launch.value.t0EpochMs.value
    const cd = typeof t0 === "number" ? t0 - ts : null

    setField(timer.value, "countdownMs", cd, ts)
    setField(timer.value, "countdownText", formatCountdown(cd), ts)
    setField(timer.value, "phase", cd === null ? "N/A" : cd >= 0 ? "T-" : "T+", ts)
  }

  // Backwards-compatible computed (ticks because timer.nowEpochMs is updated)
  const countdownMs = computed<number | null>(() => timer.value.countdownMs.value)
  const countdownText = computed<string>(() => timer.value.countdownText.value)

  // ---- clock for derived timer fields ----
  const clock = ref<{ running: boolean; intervalId: number | null }>({
    running: false,
    intervalId: null,
  })

  function startClock(): void {
    if (clock.value.running) return
    clock.value.running = true
    updateTimer(now())
    clock.value.intervalId = window.setInterval(() => updateTimer(now()), 1000)
  }

  function stopClock(): void {
    if (clock.value.intervalId != null) {
      clearInterval(clock.value.intervalId)
      clock.value.intervalId = null
    }
    clock.value.running = false
  }

  return {
    weather,
    launch,
    status,
    timer,

    meta,
    staleAfterMs,
    setStaleAfter,

    // legacy convenience (updates because timer updates)
    countdownMs,
    countdownText,

    ageMs,
    isStale,

    setWeatherField,
    setT0,
    setHold,
    markStatus,

    updateTimer,
    startClock,
    stopClock,
    clock,
  }
})
