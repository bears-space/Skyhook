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

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n))
}
function rand(min: number, max: number): number {
  return min + Math.random() * (max - min)
}
function jitter(n: number, amount: number): number {
  return n + rand(-amount, amount)
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

  // ---- simulateData(): updates values every second ----
  // Call simulateData() once to start. Call stopSimulation() to stop.
  const simulation = ref<{ running: boolean; intervalId: number | null }>({
    running: false,
    intervalId: null,
  })

  function stopSimulation(): void {
    if (simulation.value.intervalId != null) {
      clearInterval(simulation.value.intervalId)
      simulation.value.intervalId = null
    }
    simulation.value.running = false
  }

  function simulateData(options?: {
    startT0InMs?: number // default: 10 minutes
    recycleAfterLiftoffMs?: number // default: 30 seconds after T0
    holdChancePerTick?: number // default: 0.03
    releaseChancePerTick?: number // default: 0.12
  }): void {
    if (simulation.value.running) return

    const startT0InMs = options?.startT0InMs ?? 10 * 60_000
    const recycleAfterLiftoffMs = options?.recycleAfterLiftoffMs ?? 30_000
    const holdChancePerTick = options?.holdChancePerTick ?? 0.03
    const releaseChancePerTick = options?.releaseChancePerTick ?? 0.12

    const startTs = now()
    let lastTickTs = startTs

    const seed = () => {
      const ts = now()

      setWeatherField("temperatureC", rand(-5, 25), ts)
      setWeatherField("humidityPct", rand(20, 95), ts)
      setWeatherField("pressureHpa", rand(980, 1035), ts)
      setWeatherField("windSpeedMs", rand(0, 15), ts)
      setWeatherField("windGustMs", rand(0, 25), ts)
      setWeatherField("windDirDeg", rand(0, 360), ts)
      setWeatherField("precipitationMm", rand(0, 5), ts)
      setWeatherField("cloudCoverPct", rand(0, 100), ts)
      setWeatherField("visibilityM", rand(500, 20_000), ts)
      setWeatherField("lightningRisk", Math.random() < 0.05 ? true : false, ts)

      const conditions = ["Clear", "Cloudy", "Rain", "Fog", "Windy"] as const
      const picked = conditions[Math.floor(Math.random() * conditions.length)] ?? "Clear"
      setWeatherField("condition", picked, ts)

      // Timer: set initial T0 and clear hold
      setT0(ts + startT0InMs, ts)
      setHold(false, null, ts)

      markStatus({ source: "sim", health: "ok" }, ts)
      updateTimer(ts)
    }

    const recycleTimer = (ts: TsMs) => {
      setHold(false, null, ts)
      setT0(ts + startT0InMs, ts)
      updateTimer(ts)
    }

    seed()

    simulation.value.running = true
    simulation.value.intervalId = window.setInterval(() => {
      const ts = now()
      const dt = ts - lastTickTs
      lastTickTs = ts
      const t = (ts - startTs) / 1000

      // ---- weather sim ----
      const temp = weather.value.temperatureC.value ?? 10
      setWeatherField(
        "temperatureC",
        clamp(jitter(temp, 0.2) + Math.sin(t / 60) * 0.02, -20, 40),
        ts
      )

      const hum = weather.value.humidityPct.value ?? 50
      setWeatherField("humidityPct", clamp(jitter(hum, 0.8) + Math.sin(t / 45) * 0.1, 0, 100), ts)

      const p = weather.value.pressureHpa.value ?? 1013
      setWeatherField(
        "pressureHpa",
        clamp(jitter(p, 0.3) + Math.sin(t / 180) * 0.05, 930, 1060),
        ts
      )

      const ws = weather.value.windSpeedMs.value ?? 3
      const newWs = clamp(jitter(ws, 0.8), 0, 35)
      const gust = weather.value.windGustMs.value ?? newWs + 2
      const newGust = clamp(Math.max(newWs, jitter(gust, 1.5)), 0, 50)
      setWeatherField("windSpeedMs", newWs, ts)
      setWeatherField("windGustMs", newGust, ts)

      const wd = weather.value.windDirDeg.value ?? 0
      let newWd = wd + rand(-8, 8)
      if (newWd < 0) newWd += 360
      if (newWd >= 360) newWd -= 360
      setWeatherField("windDirDeg", newWd, ts)

      const cc = weather.value.cloudCoverPct.value ?? 20
      const newCc = clamp(jitter(cc, 2.0), 0, 100)
      setWeatherField("cloudCoverPct", newCc, ts)

      const visBase = 20_000 - newCc * 120
      setWeatherField("visibilityM", clamp(jitter(visBase, 300), 200, 20_000), ts)

      const precip = newCc > 75 ? clamp(rand(0, 6), 0, 20) : 0
      setWeatherField("precipitationMm", precip, ts)

      const lightning = precip > 0 && newCc > 85 && Math.random() < 0.08
      setWeatherField("lightningRisk", lightning, ts)

      const cond: string = precip > 0 ? "Rain" : newCc > 70 ? "Cloudy" : newWs > 12 ? "Windy" : "Clear"
      setWeatherField("condition", cond, ts)

      // ---- timer sim ----
      const onHold = launch.value.hold.value
      if (!onHold && Math.random() < holdChancePerTick) {
        setHold(true, "Range check", ts)
      } else if (onHold && Math.random() < releaseChancePerTick) {
        setHold(false, null, ts)
      }

      // If holding: push T0 forward so countdown freezes
      const t0 = launch.value.t0EpochMs.value
      if (launch.value.hold.value && typeof t0 === "number") {
        setT0(t0 + dt, ts)
      }

      // Recycle after liftoff + X ms
      const t0Now = launch.value.t0EpochMs.value
      if (typeof t0Now === "number" && ts - t0Now > recycleAfterLiftoffMs) {
        recycleTimer(ts)
      }

      // ✅ countdown variables tick every second (timed + timestamped)
      updateTimer(ts)

      markStatus({ source: "sim", health: "ok" }, ts)
    }, 1000)
  }

  // ---- optional: fetch example ----
  type ApiLaunchpadResponse = Partial<{
    source: string
    weather: Partial<Record<WeatherKey, WeatherState[WeatherKey]["value"]>>
    launch: Partial<{ t0EpochMs: TsMs | null; hold: boolean; holdReason: string | null }>
  }>

  async function fetchLaunchpad(url: string = "/api/launchpad"): Promise<void> {
    const ts = now()
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = (await res.json()) as ApiLaunchpadResponse

    if (data.weather) {
      for (const [k, v] of Object.entries(data.weather) as Array<
        [WeatherKey, WeatherState[WeatherKey]["value"]]
      >) {
        if (k in weather.value) setWeatherField(k, v, ts)
      }
    }

    if (data.launch) {
      if ("t0EpochMs" in data.launch) setT0(data.launch.t0EpochMs ?? null, ts)
      if ("hold" in data.launch) setHold(!!data.launch.hold, data.launch.holdReason ?? null, ts)
    }

    markStatus({ source: data.source ?? "api", health: "ok" }, ts)
    updateTimer(ts)
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
    fetchLaunchpad,

    // simulation controls
    simulateData,
    stopSimulation,
    simulation, // { running, intervalId }
  }
})
