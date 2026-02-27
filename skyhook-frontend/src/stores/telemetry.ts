// src/stores/telemetry.ts
import { defineStore } from "pinia"
import { reactive } from "vue"
import { socket } from "@/socket"
import { useLaunchpadStore } from "@/stores/launchpad"
import { useCommsStore } from "@/stores/comms"

export type MeasurementValue = number | string | boolean | Record<string, unknown> | null

export type Measurement = {
  id?: number
  ts: string
  sensor_id: number
  variable_id: number
  variable_key?: string | null
  value_type: string | null
  value: MeasurementValue
}

export type SnapshotPayload = {
  sensor_id: number
  latest: Measurement[]
}

export type MeasurementsPayload = {
  sensor_id: number
  items: Measurement[]
}

type SensorState = {
  latestByVariableId: Record<number, Measurement>
  lastUpdateMs: number
  lastSnapshotMs: number
}

function parseSensorIds(raw: string | undefined | null): number[] {
  if (!raw) return []
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => Number.parseInt(s, 10))
    .filter((n) => Number.isFinite(n) && n > 0)
}

function ensureSensor(state: Record<number, SensorState>, sensorId: number): SensorState {
  if (!state[sensorId]) {
    state[sensorId] = {
      latestByVariableId: {},
      lastUpdateMs: 0,
      lastSnapshotMs: 0,
    }
  }
  return state[sensorId]
}

function parseTsMs(ts: string | number | null | undefined): number {
  if (typeof ts === "number") return ts
  if (typeof ts === "string") {
    const parsed = Date.parse(ts)
    if (!Number.isNaN(parsed)) return parsed
  }
  return Date.now()
}

function applyLaunchpadKey(key: string, value: MeasurementValue, tsMs: number): void {
  const lp = useLaunchpadStore()

  if (key.startsWith("weather.")) {
    const weatherKey = key.replace("weather.", "")
    lp.setWeatherField(weatherKey as any, value as any, tsMs)
    return
  }

  if (key.startsWith("launch.")) {
    const launchKey = key.replace("launch.", "")
    if (launchKey === "t0EpochMs") {
      lp.setT0(typeof value === "number" ? value : value == null ? null : Number(value), tsMs)
      return
    }
    if (launchKey === "hold") {
      const currentReason = lp.launch.holdReason.value ?? null
      lp.setHold(!!value, currentReason, tsMs)
      return
    }
    if (launchKey === "holdReason") {
      const currentHold = lp.launch.hold.value
      lp.setHold(!!currentHold, value == null ? null : String(value), tsMs)
      return
    }
  }

  if (key.startsWith("status.")) {
    const statusKey = key.replace("status.", "")
    if (statusKey === "source") {
      lp.markStatus({ source: value == null ? null : String(value) }, tsMs)
      return
    }
    if (statusKey === "health") {
      lp.markStatus({ health: (value as any) ?? "ok" }, tsMs)
      return
    }
  }
}

function applyCommsKey(key: string, value: MeasurementValue, tsMs: number): void {
  const comms = useCommsStore()

  if (key.startsWith("system.")) {
    const systemKey = key.replace("system.", "")
    if (systemKey in comms.system) {
      comms.set("system", systemKey as any, value as any, tsMs)
    }
    return
  }

  const parts = key.split(".")
  if (parts.length !== 3) return
  const [g1, g2, field] = parts
  if ((g1 === "nb" || g1 === "bb") && (g2 === "up" || g2 === "down")) {
    comms.set3(g1 as any, g2 as any, field as any, value as any, tsMs)
  }
}

function dispatchVariable(item: Measurement): void {
  if (!item.variable_key) return
  const tsMs = parseTsMs(item.ts)

  if (item.variable_key.startsWith("lp.")) {
    applyLaunchpadKey(item.variable_key.replace("lp.", ""), item.value, tsMs)
    return
  }
  if (item.variable_key.startsWith("comms.")) {
    applyCommsKey(item.variable_key.replace("comms.", ""), item.value, tsMs)
  }
}

export const useTelemetryStore = defineStore("telemetry", () => {
  const sensors = reactive<Record<number, SensorState>>({})

  let listenersBound = false

  function applySnapshot(payload: SnapshotPayload): void {
    const s = ensureSensor(sensors, payload.sensor_id)
    const now = Date.now()
    s.lastSnapshotMs = now
    s.lastUpdateMs = now
    for (const item of payload.latest ?? []) {
      s.latestByVariableId[item.variable_id] = item
      dispatchVariable(item)
    }
  }

  function applyMeasurements(payload: MeasurementsPayload): void {
    const s = ensureSensor(sensors, payload.sensor_id)
    const now = Date.now()
    s.lastUpdateMs = now
    for (const item of payload.items ?? []) {
      s.latestByVariableId[item.variable_id] = item
      dispatchVariable(item)
    }
  }

  function subscribe(sensorId: number, variableIds?: number[]): void {
    if (!Number.isFinite(sensorId) || sensorId <= 0) return
    const msg: { sensor_id: number; variable_ids?: number[] } = { sensor_id: sensorId }
    if (variableIds && variableIds.length > 0) msg.variable_ids = variableIds
    socket.emit("subscribe", msg)
  }

  function subscribeAll(): void {
    const envIds = parseSensorIds(import.meta.env.VITE_SENSOR_IDS)
    if (envIds.length > 0) {
      envIds.forEach((id) => subscribe(id))
      return
    }
    socket.emit("subscribe_all")
  }

  function connect(): void {
    if (listenersBound) return
    listenersBound = true

    socket.on("connect", () => {
      subscribeAll()
    })
    socket.on("snapshot", applySnapshot)
    socket.on("measurements", applyMeasurements)

    if (socket.connected) {
      subscribeAll()
    }
  }

  function latestByKey(key: string, sensorId?: number): Measurement | null {
    const ids = sensorId ? [sensorId] : Object.keys(sensors).map((k) => Number(k))
    let best: Measurement | null = null
    let bestTs = -1
    for (const id of ids) {
      const s = sensors[id]
      if (!s) continue
      for (const item of Object.values(s.latestByVariableId)) {
        if (item.variable_key !== key) continue
        const ts = parseTsMs(item.ts)
        if (ts > bestTs) {
          bestTs = ts
          best = item
        }
      }
    }
    return best
  }

  function valueByKey<T = MeasurementValue>(key: string, sensorId?: number): T | null {
    const item = latestByKey(key, sensorId)
    return item ? (item.value as T) : null
  }

  return {
    connect,
    latestByKey,
    valueByKey,
  }
})
