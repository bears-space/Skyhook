// src/stores/comms.ts
import { defineStore } from "pinia"
import { computed, reactive, ref } from "vue"

export type TsMs = number
export type TimedMeta = { ts: TsMs; ageMs: number | null; isStale: boolean }
export type LinkHealth = "ok" | "degraded" | "offline"
export type LinkState = "idle" | "acquiring" | "locked" | "tx" | "rx" | "error"

const now = (): TsMs => Date.now()

export type Field<T> = {
  value: T
  ts: TsMs
  staleAfterMs: number
}

export type FieldSpec<T> = {
  initial: T
  staleAfterMs: number
}

export const F = <T>(initial: T, staleAfterMs: number): FieldSpec<T> => ({
  initial,
  staleAfterMs,
})

function makeField<T>(spec: FieldSpec<T>): Field<T> {
  return { value: spec.initial, ts: 0, staleAfterMs: spec.staleAfterMs }
}

function setField<T>(f: Field<T>, value: T, ts: TsMs = now()): void {
  f.value = value
  f.ts = ts
}

function metaFor<T>(f: Field<T>): TimedMeta {
  const age = f.ts ? now() - f.ts : null
  const isStale = age === null ? true : age > f.staleAfterMs
  return { ts: f.ts, ageMs: age, isStale }
}

type SpecTree = Record<string, any>
type StateFromSpecs<S> = {
  [K in keyof S]: S[K] extends FieldSpec<infer T>
    ? Field<T>
    : S[K] extends SpecTree
      ? StateFromSpecs<S[K]>
      : never
}

function isFieldSpec(x: any): x is FieldSpec<any> {
  return x && typeof x === "object" && "initial" in x && "staleAfterMs" in x
}

function makeState<S extends SpecTree>(specs: S): StateFromSpecs<S> {
  const out: any = {}
  for (const [k, v] of Object.entries(specs)) {
    out[k] = isFieldSpec(v) ? makeField(v) : makeState(v as SpecTree)
  }
  return out
}

type MetaFromState<T> = {
  [K in keyof T]: T[K] extends Field<any> ? TimedMeta : MetaFromState<T[K]>
}

function buildMeta<T extends Record<string, any>>(stateObj: T): MetaFromState<T> {
  const out: any = {}
  for (const [k, v] of Object.entries(stateObj)) {
    out[k] =
      v && typeof v === "object" && "value" in v && "staleAfterMs" in v
        ? metaFor(v as Field<any>)
        : buildMeta(v)
  }
  return out
}

// -----------------------------
// ✅ SPECS: adding variables = adding one line
// -----------------------------
const specs = {
  nb: {
    // Uplink (ground -> vehicle)
    up: {
      health: F<LinkHealth>("offline", 5_000),
      state: F<LinkState>("idle", 3_000),

      // Data rates
      rateBps: F<number | null>(null, 2_000),
      rateAvgBps: F<number | null>(null, 10_000),
      utilPct: F<number | null>(null, 2_000), // 0..100

      // RF quality
      rssiDbm: F<number | null>(null, 5_000),
      snrDb: F<number | null>(null, 5_000),

      // Error/quality
      ber: F<number | null>(null, 10_000), // bit error rate
      per: F<number | null>(null, 10_000), // packet error rate
      packetLossPct: F<number | null>(null, 10_000),

      // Timing
      latencyMs: F<number | null>(null, 10_000),
      jitterMs: F<number | null>(null, 10_000),

      // System
      freqHz: F<number | null>(null, 60_000),
      bandwidthHz: F<number | null>(null, 60_000),
      modcod: F<string | null>(null, 60_000), // e.g. "QPSK 1/2", "LoRa SF7 CR4/5"

      lastTxEpochMs: F<TsMs | null>(null, 5_000),
      lastRxEpochMs: F<TsMs | null>(null, 5_000),
    },

    // Downlink (vehicle -> ground)
    down: {
      health: F<LinkHealth>("offline", 5_000),
      state: F<LinkState>("idle", 3_000),

      rateBps: F<number | null>(null, 2_000),
      rateAvgBps: F<number | null>(null, 10_000),
      utilPct: F<number | null>(null, 2_000),

      // Often NB is cellular-ish (optional fields)
      rsrpDbm: F<number | null>(null, 10_000),
      rsrqDb: F<number | null>(null, 10_000),
      sinrDb: F<number | null>(null, 10_000),

      rssiDbm: F<number | null>(null, 5_000),
      snrDb: F<number | null>(null, 5_000),

      ber: F<number | null>(null, 10_000),
      per: F<number | null>(null, 10_000),
      packetLossPct: F<number | null>(null, 10_000),

      latencyMs: F<number | null>(null, 10_000),
      jitterMs: F<number | null>(null, 10_000),

      freqHz: F<number | null>(null, 60_000),
      bandwidthHz: F<number | null>(null, 60_000),
      modcod: F<string | null>(null, 60_000),

      lastTxEpochMs: F<TsMs | null>(null, 5_000),
      lastRxEpochMs: F<TsMs | null>(null, 5_000),
    },
  },

  bb: {
    // Broadband downlink (vehicle -> ground)
    down: {
      health: F<LinkHealth>("offline", 5_000),
      state: F<LinkState>("idle", 2_000),

      rateBps: F<number | null>(null, 1_000),
      rateAvgBps: F<number | null>(null, 10_000),
      utilPct: F<number | null>(null, 1_000),

      // Wi-Fi / microwave / SDR-ish quality
      rssiDbm: F<number | null>(null, 3_000),
      snrDb: F<number | null>(null, 3_000),
      mcs: F<number | null>(null, 10_000), // Wi-Fi MCS index, or similar
      phyRateBps: F<number | null>(null, 10_000),

      // Error/quality
      per: F<number | null>(null, 5_000),
      packetLossPct: F<number | null>(null, 5_000),

      latencyMs: F<number | null>(null, 5_000),
      jitterMs: F<number | null>(null, 5_000),

      // System
      freqHz: F<number | null>(null, 60_000),
      bandwidthHz: F<number | null>(null, 60_000),
      channel: F<number | null>(null, 60_000),

      lastTxEpochMs: F<TsMs | null>(null, 3_000),
      lastRxEpochMs: F<TsMs | null>(null, 3_000),
    },
  },

  // Overall / shared comms info
  system: {
    source: F<string | null>(null, 60_000), // "sim", "radio", "api"
    lastUpdateEpochMs: F<TsMs | null>(null, 3_000),
    notes: F<string | null>(null, 60_000),
  },
} as const

export const useCommsStore = defineStore("comms", () => {
  const state = reactive(makeState(specs))
  const tick = ref(0)
  const meta = computed(() => {
    // Ensure isStale/ageMs keep updating even when no new data arrives.
    void tick.value
    return buildMeta(state)
  })

  function set<
    G extends keyof typeof state,
    K extends keyof (typeof state)[G]
  >(
    group: G,
    key: K,
    value: (typeof state)[G][K] extends Field<infer T> ? T : never,
    ts: TsMs = now()
  ): void {
    setField((state[group] as any)[key] as Field<any>, value, ts)
    setField(state.system.lastUpdateEpochMs, ts, ts)
  }

  // Nested setter for deeper paths like ("nb","up","rateBps", 123)
  function set3<
    G1 extends keyof typeof state,
    G2 extends keyof (typeof state)[G1],
    K extends keyof (typeof state)[G1][G2]
  >(
    g1: G1,
    g2: G2,
    key: K,
    value: (typeof state)[G1][G2][K] extends Field<infer T> ? T : never,
    ts: TsMs = now()
  ): void {
    setField(((state[g1] as any)[g2] as any)[key] as Field<any>, value, ts)
    setField(state.system.lastUpdateEpochMs, ts, ts)
  }

  function setStaleAfter3<
    G1 extends keyof typeof state,
    G2 extends keyof (typeof state)[G1],
    K extends keyof (typeof state)[G1][G2]
  >(g1: G1, g2: G2, key: K, staleAfterMs: number): void {
    ;(((state[g1] as any)[g2] as any)[key] as Field<any>).staleAfterMs = staleAfterMs
  }

  // Convenience computed summaries
  const nbUpRateBps = computed(() => state.nb.up.rateBps.value)
  const nbDownRateBps = computed(() => state.nb.down.rateBps.value)
  const bbDownRateBps = computed(() => state.bb.down.rateBps.value)

  const overallHealth = computed<LinkHealth>(() => {
    const h = [state.nb.up.health.value, state.nb.down.health.value, state.bb.down.health.value]
    if (h.includes("offline")) return "offline"
    if (h.includes("degraded")) return "degraded"
    return "ok"
  })

  const clock = ref<{ running: boolean; intervalId: number | null }>({
    running: false,
    intervalId: null,
  })

  function startClock(): void {
    if (clock.value.running) return
    clock.value.running = true
    tick.value = now()
    clock.value.intervalId = window.setInterval(() => {
      tick.value = now()
    }, 1000)
  }

  function stopClock(): void {
    if (clock.value.intervalId != null) {
      clearInterval(clock.value.intervalId)
      clock.value.intervalId = null
    }
    clock.value.running = false
  }

  return {
    // groups
    nb: state.nb,
    bb: state.bb,
    system: state.system,

    meta,

    // setters
    set, // for shallow (system)
    set3, // for nb/bb link fields
    setStaleAfter3,

    // summaries
    nbUpRateBps,
    nbDownRateBps,
    bbDownRateBps,
    overallHealth,

    // stale-age ticking
    startClock,
    stopClock,
    clock,
  }
})
