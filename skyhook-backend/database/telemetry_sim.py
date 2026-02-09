#!/usr/bin/env python3
"""
telemetry_sim.py
Dev telemetry generator that inserts typed measurements into MariaDB every N ms.

- Creates sensor + variables if missing (ON DUPLICATE KEY).
- Generates realistic-ish rocket-ish telemetry:
  altitude, velocity, acceleration, battery, temperature, status, armed, GPS JSON, packet counter, RSSI.
- Inserts into measurements table with value_type + exactly one value_* column (trigger safe).

Env vars (defaults match your init_db.py):
  DB_HOST=db
  DB_PORT=3306
  DB_USER=skyhook
  DB_PASS=skyhookpass
  DB_NAME=skyhook

Usage:
  python telemetry_sim.py
  python telemetry_sim.py --dry-run
  python telemetry_sim.py --period-ms 300 --batch 10
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import pymysql
from pymysql.constants import CLIENT


# -----------------------------
# Config helpers
# -----------------------------
def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def utc_now_dt3() -> str:
    # MariaDB DATETIME(3) wants "YYYY-MM-DD HH:MM:SS.mmm"
    # Use UTC to avoid timezone surprises.
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(dt.microsecond/1000):03d}"


# -----------------------------
# Variable definitions
# -----------------------------
DataType = str  # 'num'|'int'|'bool'|'text'|'json'|'blob'


@dataclass
class VarDef:
    key: str
    name: str
    unit: Optional[str]
    data_type: DataType
    desc: str = ""
    # generator returns the typed value (float/int/bool/str/dict/bytes)
    gen: Callable[["SimState"], Any] = lambda s: None


@dataclass
class SimState:
    t0: float = field(default_factory=time.monotonic)
    tick: int = 0
    phase: str = "idle"  # idle -> countdown -> ascent -> coast -> descent -> landed
    armed: bool = False
    last_phase_change_t: float = field(default_factory=time.monotonic)

    # "physical-ish" state
    altitude_m: float = 0.0
    velocity_mps: float = 0.0
    accel_mps2: float = 0.0

    # misc
    battery_v: float = 4.20
    temp_c: float = 22.0
    rssi_dbm: float = -60.0
    packet_counter: int = 0
    status: str = "BOOT"

    # GPS-ish
    lat: float = 52.5200
    lon: float = 13.4050
    gps_fix: int = 0  # 0=no, 2=2D, 3=3D
    hdop: float = 99.0

    def t(self) -> float:
        return time.monotonic() - self.t0


# -----------------------------
# Telemetry model (simple state machine)
# -----------------------------
def update_sim(state: SimState, dt: float) -> None:
    """
    Update state with a simple flight-like profile.
    dt is seconds (e.g. 0.300).
    """
    t = state.t()

    # phase transitions (simple timeline)
    # 0-3s idle, 3-8s countdown, 8-28s ascent, 28-34s coast, 34-80s descent, then landed
    if t < 3.0:
        state.phase = "idle"
        state.armed = False
        state.status = "IDLE"
    elif t < 8.0:
        state.phase = "countdown"
        state.armed = True
        state.status = f"T-{max(0, int(8 - t))}"
    elif t < 28.0:
        state.phase = "ascent"
        state.armed = True
        state.status = "ASCENT"
    elif t < 34.0:
        state.phase = "coast"
        state.armed = True
        state.status = "COAST"
    elif t < 80.0:
        state.phase = "descent"
        state.armed = True
        state.status = "DESCENT"
    else:
        state.phase = "landed"
        state.armed = False
        state.status = "LANDED"

    # Add occasional “events”
    if state.phase in ("ascent", "descent") and random.random() < 0.01:
        state.status = random.choice(["NOMINAL", "WARN_VIB", "WARN_TEMP", "LINK_WEAK"])

    # Dynamics (very simplified)
    # Choose a target acceleration profile based on phase
    if state.phase == "idle":
        a = 0.0
    elif state.phase == "countdown":
        a = 0.0
    elif state.phase == "ascent":
        # thrust + noise: ~15 m/s^2 average early, taper down
        a = 18.0 * math.exp(-(t - 8.0) / 18.0) + random.gauss(0.0, 0.6)
    elif state.phase == "coast":
        # near ballistic: gravity only, slightly noisy
        a = -9.81 + random.gauss(0.0, 0.2)
    elif state.phase == "descent":
        # parachute-like: approach terminal velocity ~ -18 m/s
        # use a PD-ish pull towards terminal velocity
        terminal = -18.0 + random.gauss(0.0, 0.4)
        a = (terminal - state.velocity_mps) * 0.8 + random.gauss(0.0, 0.3)
    else:  # landed
        a = 0.0
        state.velocity_mps = 0.0
        state.altitude_m = max(0.0, state.altitude_m)

    state.accel_mps2 = a
    state.velocity_mps += state.accel_mps2 * dt
    state.altitude_m += state.velocity_mps * dt

    # Floor at ground
    if state.altitude_m < 0.0:
        state.altitude_m = 0.0
        state.velocity_mps = 0.0

    # Battery drains slowly, faster when armed
    drain = 0.0006 + (0.0012 if state.armed else 0.0004)
    state.battery_v = max(3.30, state.battery_v - drain * dt)

    # Temperature varies
    temp_target = 25.0 if state.armed else 22.0
    if state.phase == "ascent":
        temp_target += 8.0
    if state.phase == "descent":
        temp_target -= 2.0
    state.temp_c += (temp_target - state.temp_c) * 0.02 + random.gauss(0.0, 0.05)

    # RSSI: degrade with “altitude” a bit + noise
    state.rssi_dbm = -55.0 - 0.015 * state.altitude_m + random.gauss(0.0, 1.5)
    state.rssi_dbm = max(-120.0, min(-30.0, state.rssi_dbm))

    # Packet counter
    state.packet_counter += 1

    # GPS: becomes valid after countdown, loses precision under dynamics
    if state.phase in ("idle",):
        state.gps_fix = 0
        state.hdop = 99.0
    elif state.phase in ("countdown", "landed"):
        state.gps_fix = 3
        state.hdop = 0.8 + random.random() * 0.3
    else:
        state.gps_fix = 3
        state.hdop = 1.2 + random.random() * 1.0

    # GPS drift (tiny random walk)
    state.lat += random.gauss(0.0, 0.000001)
    state.lon += random.gauss(0.0, 0.000001)


# -----------------------------
# DB layer
# -----------------------------
class DB:
    def __init__(self) -> None:
        self.host = _env("DB_HOST", "db")
        self.port = int(_env("DB_PORT", "3306"))
        self.user = _env("DB_USER", "skyhook")
        self.password = _env("DB_PASS", "skyhookpass")
        self.database = _env("DB_NAME", "skyhook")

        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=True,
            client_flag=CLIENT.MULTI_STATEMENTS,
        )

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def ensure_sensor(self, name: str, description: str = "") -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sensors (name, description)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE description = VALUES(description)
                """,
                (name, description),
            )
            cur.execute("SELECT id FROM sensors WHERE name=%s LIMIT 1", (name,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Failed to resolve sensor id")
            return int(row[0])

    def ensure_variable(self, v: VarDef) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO variables (`key`, name, unit, data_type, description)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  name = VALUES(name),
                  unit = VALUES(unit),
                  data_type = VALUES(data_type),
                  description = VALUES(description)
                """,
                (v.key, v.name, v.unit, v.data_type, v.desc),
            )
            cur.execute("SELECT id FROM variables WHERE `key`=%s LIMIT 1", (v.key,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Failed to resolve variable id for {v.key}")
            return int(row[0])

    def insert_measurements_batch(
        self,
        rows: List[Tuple[str, int, int, str, Optional[float], Optional[int], Optional[int], Optional[str], Optional[str], Optional[bytes]]],
    ) -> None:
        """
        rows: (ts, sensor_id, variable_id, value_type, value_num, value_int, value_bool, value_text, value_json, value_blob)
        """
        if not rows:
            return
        with self.conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO measurements
                  (ts, sensor_id, variable_id, value_type,
                   value_num, value_int, value_bool, value_text, value_json, value_blob)
                VALUES
                  (%s, %s, %s, %s,
                   %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )


# -----------------------------
# Main simulator
# -----------------------------
def build_variables() -> List[VarDef]:
    # Define your variables here (the “list of variables”).
    # data_type must match your schema + triggers: 'num','int','bool','text','json','blob'
    return [
        VarDef(
            key="altitude_m",
            name="Altitude",
            unit="m",
            data_type="num",
            desc="Simulated altitude above ground",
            gen=lambda s: max(0.0, s.altitude_m + random.gauss(0.0, 0.8)),
        ),
        VarDef(
            key="velocity_mps",
            name="Vertical Velocity",
            unit="m/s",
            data_type="num",
            desc="Simulated vertical velocity",
            gen=lambda s: s.velocity_mps + random.gauss(0.0, 0.3),
        ),
        VarDef(
            key="accel_mps2",
            name="Acceleration",
            unit="m/s^2",
            data_type="num",
            desc="Simulated vertical acceleration",
            gen=lambda s: s.accel_mps2 + random.gauss(0.0, 0.2),
        ),
        VarDef(
            key="battery_v",
            name="Battery Voltage",
            unit="V",
            data_type="num",
            desc="Battery pack voltage",
            gen=lambda s: round(s.battery_v + random.gauss(0.0, 0.01), 3),
        ),
        VarDef(
            key="temp_c",
            name="Temperature",
            unit="°C",
            data_type="num",
            desc="Board temperature",
            gen=lambda s: round(s.temp_c, 2),
        ),
        VarDef(
            key="armed",
            name="Armed",
            unit=None,
            data_type="bool",
            desc="Arming state",
            gen=lambda s: 1 if s.armed else 0,
        ),
        VarDef(
            key="status",
            name="Status",
            unit=None,
            data_type="text",
            desc="Human-readable system status",
            gen=lambda s: s.status,
        ),
        VarDef(
            key="rssi_dbm",
            name="RSSI",
            unit="dBm",
            data_type="num",
            desc="Link RSSI estimate",
            gen=lambda s: round(s.rssi_dbm, 1),
        ),
        VarDef(
            key="packet_counter",
            name="Packet Counter",
            unit=None,
            data_type="int",
            desc="Monotonic packet counter",
            gen=lambda s: s.packet_counter,
        ),
        VarDef(
            key="gps_fix",
            name="GPS Fix",
            unit=None,
            data_type="json",
            desc="GPS fix info as JSON",
            gen=lambda s: {
                "fix": s.gps_fix,
                "lat": round(s.lat, 6),
                "lon": round(s.lon, 6),
                "hdop": round(s.hdop, 2),
            },
        ),
    ]


def to_measurement_row(
    ts: str,
    sensor_id: int,
    variable_id: int,
    value_type: str,
    value: Any,
) -> Tuple[str, int, int, str, Optional[float], Optional[int], Optional[int], Optional[str], Optional[str], Optional[bytes]]:
    """
    Maps (value_type, value) to the correct value_* column.
    Ensures only one value_* is non-null.
    """
    value_num = value_int = value_bool = None
    value_text = value_json = None
    value_blob = None

    if value_type == "num":
        value_num = float(value)
    elif value_type == "int":
        value_int = int(value)
    elif value_type == "bool":
        # store 0/1
        value_bool = 1 if bool(value) else 0
    elif value_type == "text":
        value_text = str(value)
    elif value_type == "json":
        value_json = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    elif value_type == "blob":
        if isinstance(value, (bytes, bytearray)):
            value_blob = bytes(value)
        else:
            raise TypeError("blob value must be bytes/bytearray")
    else:
        raise ValueError(f"Unknown value_type: {value_type}")

    return (ts, sensor_id, variable_id, value_type, value_num, value_int, value_bool, value_text, value_json, value_blob)


def run() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period-ms", type=int, default=300, help="Tick period in milliseconds (default: 300)")
    ap.add_argument("--batch", type=int, default=10, help="Batch size for DB inserts (default: 10 ticks)")
    ap.add_argument("--dry-run", action="store_true", help="Do not connect/insert into DB; just print samples")
    ap.add_argument("--sensor-name", default="sim-avionics", help="Sensor name to use/create in DB")
    ap.add_argument("--max-seconds", type=float, default=0.0, help="Stop after N seconds (0 = infinite)")
    ap.add_argument("--print-every", type=int, default=10, help="Print one line every N ticks (default: 10)")
    args = ap.parse_args()

    period_s = args.period_ms / 1000.0
    variables = build_variables()

    stop = False

    def _sig(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    state = SimState()
    next_t = time.monotonic()

    db: Optional[DB] = None
    sensor_id = 0
    var_ids: Dict[str, int] = {}

    if not args.dry_run:
        db = DB()
        sensor_id = db.ensure_sensor(args.sensor_name, "Simulated telemetry source")
        for v in variables:
            var_ids[v.key] = db.ensure_variable(v)

    pending_rows: List[Tuple[str, int, int, str, Optional[float], Optional[int], Optional[int], Optional[str], Optional[str], Optional[bytes]]] = []

    print(f"[telemetry_sim] period={args.period_ms}ms batch={args.batch} dry_run={args.dry_run} sensor={args.sensor_name} 🚀")

    start_t = time.monotonic()
    while not stop:
        now = time.monotonic()
        if args.max_seconds > 0 and (now - start_t) >= args.max_seconds:
            break

        # drift-less scheduling
        if now < next_t:
            time.sleep(next_t - now)

        tick_start = time.monotonic()

        # update sim
        dt = period_s
        update_sim(state, dt)
        state.tick += 1

        ts = utc_now_dt3()

        # build rows (one per variable)
        sample: Dict[str, Any] = {}
        for v in variables:
            val = v.gen(state)
            sample[v.key] = val
            if not args.dry_run:
                row = to_measurement_row(
                    ts=ts,
                    sensor_id=sensor_id,
                    variable_id=var_ids[v.key],
                    value_type=v.data_type,
                    value=val,
                )
                pending_rows.append(row)

        # Print occasionally (dev feedback)
        if state.tick % args.print_every == 0:
            # compact preview
            preview = {
                "t": round(state.t(), 1),
                "phase": state.phase,
                "alt": round(float(sample["altitude_m"]), 1),
                "vel": round(float(sample["velocity_mps"]), 1),
                "batt": float(sample["battery_v"]),
                "rssi": float(sample["rssi_dbm"]),
                "status": sample["status"],
            }
            print("[telemetry_sim]", json.dumps(preview, ensure_ascii=False))

        # Flush batch
        if not args.dry_run and db and len(pending_rows) >= (args.batch * len(variables)):
            db.insert_measurements_batch(pending_rows)
            pending_rows.clear()

        # schedule next tick
        next_t += period_s

        # In case computation takes too long, resync (avoid spiraling lag)
        tick_end = time.monotonic()
        if tick_end - tick_start > period_s * 0.9:
            next_t = tick_end + period_s

    # final flush
    if not args.dry_run and db and pending_rows:
        db.insert_measurements_batch(pending_rows)
        pending_rows.clear()

    if db:
        db.close()

    print("[telemetry_sim] stopped ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
