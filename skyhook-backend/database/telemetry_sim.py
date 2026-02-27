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


def unix_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def clamp(n: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, n))


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

    # launchpad-ish
    launch_t0_epoch_ms: Optional[int] = None
    launch_hold: bool = False
    launch_hold_reason: str = ""

    # weather-ish
    weather_temp_c: float = 18.0
    weather_humidity_pct: float = 55.0
    weather_pressure_hpa: float = 1012.0
    weather_wind_speed_ms: float = 4.0
    weather_wind_dir_deg: float = 180.0
    weather_cloud_cover_pct: float = 40.0

    # comms-ish
    comms_notes: str = ""
    epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))

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
    state.epoch_ms = int(time.time() * 1000)

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
    # launchpad-ish (countdown + hold)
    # -----------------------------
    if state.launch_t0_epoch_ms is None:
        state.launch_t0_epoch_ms = state.epoch_ms + 10 * 60_000
        state.launch_hold = False
        state.launch_hold_reason = ""

    if not state.launch_hold and random.random() < 0.02:
        state.launch_hold = True
        state.launch_hold_reason = random.choice(["Range check", "Wind constraint", "Comms verify"])
    elif state.launch_hold and random.random() < 0.08:
        state.launch_hold = False
        state.launch_hold_reason = ""

    if state.launch_hold and state.launch_t0_epoch_ms is not None:
        state.launch_t0_epoch_ms += int(dt * 1000)

    if state.launch_t0_epoch_ms is not None and state.epoch_ms - state.launch_t0_epoch_ms > 30_000:
        state.launch_t0_epoch_ms = state.epoch_ms + 10 * 60_000
        state.launch_hold = False
        state.launch_hold_reason = ""

    # -----------------------------
    # weather-ish slow drift
    # -----------------------------
    state.weather_temp_c = clamp(state.weather_temp_c + random.gauss(0.0, 0.03), -20, 40)
    state.weather_humidity_pct = clamp(state.weather_humidity_pct + random.gauss(0.0, 0.2), 5, 100)
    state.weather_pressure_hpa = clamp(state.weather_pressure_hpa + random.gauss(0.0, 0.05), 930, 1060)
    state.weather_wind_speed_ms = clamp(state.weather_wind_speed_ms + random.gauss(0.0, 0.15), 0, 35)
    state.weather_wind_dir_deg = (state.weather_wind_dir_deg + random.gauss(0.0, 1.5)) % 360
    state.weather_cloud_cover_pct = clamp(state.weather_cloud_cover_pct + random.gauss(0.0, 0.8), 0, 100)


def comms_quality(t: float, period: float, phase: float = 0.0) -> float:
    # 0..1
    return 0.5 + 0.5 * math.sin((t + phase) / period)


def comms_health(q: float) -> str:
    if q < 0.2:
        return "offline"
    if q < 0.45:
        return "degraded"
    return "ok"


def comms_state(t: float, offset: float = 0.0) -> str:
    states = ["idle", "tx", "rx", "locked", "acquiring"]
    idx = int((t + offset) / 8.0) % len(states)
    return states[idx]


def comms_modcod(q: float) -> str:
    if q < 0.3:
        return "BPSK 1/2"
    if q < 0.55:
        return "QPSK 1/2"
    if q < 0.75:
        return "QPSK 3/4"
    return "16QAM 1/2"


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
        rows: List[Tuple[int, int, int, str, Optional[float], Optional[int], Optional[int], Optional[str], Optional[str], Optional[bytes]]],
    ) -> None:
        """
        rows: (ts_ms, sensor_id, variable_id, value_type, value_num, value_int, value_bool, value_text, value_json, value_blob)
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
    def q_nb_up(s: SimState) -> float:
        return comms_quality(s.t(), 18.0, 0.0)

    def q_nb_down(s: SimState) -> float:
        return comms_quality(s.t(), 22.0, 2.5)

    def q_bb_down(s: SimState) -> float:
        return comms_quality(s.t(), 14.0, 1.0)

    def nb_up_rate(s: SimState) -> float:
        return 60_000 + 90_000 * q_nb_up(s) + random.gauss(0.0, 2000)

    def nb_down_rate(s: SimState) -> float:
        return 90_000 + 120_000 * q_nb_down(s) + random.gauss(0.0, 2500)

    def bb_down_rate(s: SimState) -> float:
        return 3_500_000 + 2_500_000 * q_bb_down(s) + random.gauss(0.0, 50_000)

    def precip_mm(s: SimState) -> float:
        cc = s.weather_cloud_cover_pct
        base = max(0.0, (cc - 70.0) / 12.0)
        return round(min(12.0, base), 2)

    def visibility_m(s: SimState) -> float:
        cc = s.weather_cloud_cover_pct
        return round(clamp(20_000 - cc * 120 + random.gauss(0.0, 200), 200, 20_000), 0)

    def condition(s: SimState) -> str:
        p = precip_mm(s)
        if p > 0.4:
            return "Rain"
        if s.weather_cloud_cover_pct > 70:
            return "Cloudy"
        if s.weather_wind_speed_ms > 12:
            return "Windy"
        return "Clear"

    vars: List[VarDef] = [
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

    # -----------------------------
    # Launchpad / weather variables (DB-backed)
    # -----------------------------
    vars.extend(
        [
            VarDef(
                key="lp.weather.temperatureC",
                name="Weather Temp",
                unit="°C",
                data_type="num",
                desc="Ambient temperature",
                gen=lambda s: round(s.weather_temp_c, 2),
            ),
            VarDef(
                key="lp.weather.humidityPct",
                name="Humidity",
                unit="%",
                data_type="num",
                desc="Relative humidity",
                gen=lambda s: round(s.weather_humidity_pct, 1),
            ),
            VarDef(
                key="lp.weather.pressureHpa",
                name="Pressure",
                unit="hPa",
                data_type="num",
                desc="Barometric pressure",
                gen=lambda s: round(s.weather_pressure_hpa, 2),
            ),
            VarDef(
                key="lp.weather.windSpeedMs",
                name="Wind Speed",
                unit="m/s",
                data_type="num",
                desc="Surface wind speed",
                gen=lambda s: round(s.weather_wind_speed_ms, 2),
            ),
            VarDef(
                key="lp.weather.windGustMs",
                name="Wind Gust",
                unit="m/s",
                data_type="num",
                desc="Wind gust speed",
                gen=lambda s: round(s.weather_wind_speed_ms + random.uniform(0.5, 4.0), 2),
            ),
            VarDef(
                key="lp.weather.windDirDeg",
                name="Wind Direction",
                unit="deg",
                data_type="num",
                desc="Wind direction (deg)",
                gen=lambda s: round(s.weather_wind_dir_deg, 1),
            ),
            VarDef(
                key="lp.weather.precipitationMm",
                name="Precipitation",
                unit="mm",
                data_type="num",
                desc="Precipitation rate",
                gen=lambda s: precip_mm(s),
            ),
            VarDef(
                key="lp.weather.cloudCoverPct",
                name="Cloud Cover",
                unit="%",
                data_type="num",
                desc="Cloud cover",
                gen=lambda s: round(s.weather_cloud_cover_pct, 0),
            ),
            VarDef(
                key="lp.weather.visibilityM",
                name="Visibility",
                unit="m",
                data_type="num",
                desc="Estimated visibility",
                gen=lambda s: visibility_m(s),
            ),
            VarDef(
                key="lp.weather.lightningRisk",
                name="Lightning Risk",
                unit=None,
                data_type="bool",
                desc="Lightning risk flag",
                gen=lambda s: 1 if precip_mm(s) > 1.0 and s.weather_cloud_cover_pct > 80 and random.random() < 0.1 else 0,
            ),
            VarDef(
                key="lp.weather.condition",
                name="Weather Condition",
                unit=None,
                data_type="text",
                desc="Weather condition",
                gen=lambda s: condition(s),
            ),
            VarDef(
                key="lp.launch.t0EpochMs",
                name="Launch T0",
                unit="ms",
                data_type="int",
                desc="Planned T0 epoch milliseconds",
                gen=lambda s: int(s.launch_t0_epoch_ms or s.epoch_ms),
            ),
            VarDef(
                key="lp.launch.hold",
                name="Launch Hold",
                unit=None,
                data_type="bool",
                desc="Launch hold flag",
                gen=lambda s: 1 if s.launch_hold else 0,
            ),
            VarDef(
                key="lp.launch.holdReason",
                name="Hold Reason",
                unit=None,
                data_type="text",
                desc="Launch hold reason",
                gen=lambda s: s.launch_hold_reason or "",
            ),
            VarDef(
                key="lp.status.source",
                name="Launchpad Source",
                unit=None,
                data_type="text",
                desc="Launchpad source",
                gen=lambda s: "sim",
            ),
            VarDef(
                key="lp.status.health",
                name="Launchpad Health",
                unit=None,
                data_type="text",
                desc="Launchpad health",
                gen=lambda s: "ok" if not s.launch_hold else "degraded",
            ),
        ]
    )

    # -----------------------------
    # Comms variables (DB-backed)
    # -----------------------------
    vars.extend(
        [
            # system
            VarDef(
                key="comms.system.source",
                name="Comms Source",
                unit=None,
                data_type="text",
                desc="Comms telemetry source",
                gen=lambda s: "sim",
            ),
            VarDef(
                key="comms.system.notes",
                name="Comms Notes",
                unit=None,
                data_type="text",
                desc="Comms notes",
                gen=lambda s: s.comms_notes or "Nominal",
            ),
            # NB uplink
            VarDef(
                key="comms.nb.up.health",
                name="NB Up Health",
                unit=None,
                data_type="text",
                desc="NB uplink health",
                gen=lambda s: comms_health(q_nb_up(s)),
            ),
            VarDef(
                key="comms.nb.up.state",
                name="NB Up State",
                unit=None,
                data_type="text",
                desc="NB uplink state",
                gen=lambda s: comms_state(s.t(), 0.0),
            ),
            VarDef(
                key="comms.nb.up.rateBps",
                name="NB Up Rate",
                unit="b/s",
                data_type="num",
                desc="NB uplink rate",
                gen=lambda s: round(nb_up_rate(s), 0),
            ),
            VarDef(
                key="comms.nb.up.rateAvgBps",
                name="NB Up Rate Avg",
                unit="b/s",
                data_type="num",
                desc="NB uplink avg rate",
                gen=lambda s: round(60_000 + 90_000 * comms_quality(s.t(), 45.0, 0.0), 0),
            ),
            VarDef(
                key="comms.nb.up.utilPct",
                name="NB Up Util",
                unit="%",
                data_type="num",
                desc="NB uplink utilization",
                gen=lambda s: round(clamp(nb_up_rate(s) / 200_000 * 100.0, 0, 100), 1),
            ),
            VarDef(
                key="comms.nb.up.rssiDbm",
                name="NB Up RSSI",
                unit="dBm",
                data_type="num",
                desc="NB uplink RSSI",
                gen=lambda s: round(-95.0 + 20.0 * q_nb_up(s) + random.gauss(0.0, 1.2), 1),
            ),
            VarDef(
                key="comms.nb.up.snrDb",
                name="NB Up SNR",
                unit="dB",
                data_type="num",
                desc="NB uplink SNR",
                gen=lambda s: round(2.0 + 10.0 * q_nb_up(s) + random.gauss(0.0, 0.3), 1),
            ),
            VarDef(
                key="comms.nb.up.ber",
                name="NB Up BER",
                unit=None,
                data_type="num",
                desc="NB uplink BER",
                gen=lambda s: round(max(1e-6, (1.0 - q_nb_up(s)) * 1e-3), 6),
            ),
            VarDef(
                key="comms.nb.up.per",
                name="NB Up PER",
                unit="%",
                data_type="num",
                desc="NB uplink PER",
                gen=lambda s: round((1.0 - q_nb_up(s)) * 2.5, 2),
            ),
            VarDef(
                key="comms.nb.up.packetLossPct",
                name="NB Up Packet Loss",
                unit="%",
                data_type="num",
                desc="NB uplink packet loss",
                gen=lambda s: round((1.0 - q_nb_up(s)) * 5.0, 2),
            ),
            VarDef(
                key="comms.nb.up.latencyMs",
                name="NB Up Latency",
                unit="ms",
                data_type="num",
                desc="NB uplink latency",
                gen=lambda s: round(120.0 + (1.0 - q_nb_up(s)) * 180.0, 0),
            ),
            VarDef(
                key="comms.nb.up.jitterMs",
                name="NB Up Jitter",
                unit="ms",
                data_type="num",
                desc="NB uplink jitter",
                gen=lambda s: round(6.0 + (1.0 - q_nb_up(s)) * 18.0, 0),
            ),
            VarDef(
                key="comms.nb.up.freqHz",
                name="NB Up Frequency",
                unit="Hz",
                data_type="num",
                desc="NB uplink center frequency",
                gen=lambda s: 433_920_000,
            ),
            VarDef(
                key="comms.nb.up.bandwidthHz",
                name="NB Up Bandwidth",
                unit="Hz",
                data_type="num",
                desc="NB uplink bandwidth",
                gen=lambda s: 125_000,
            ),
            VarDef(
                key="comms.nb.up.modcod",
                name="NB Up Mod/Cod",
                unit=None,
                data_type="text",
                desc="NB uplink modulation/coding",
                gen=lambda s: comms_modcod(q_nb_up(s)),
            ),
            VarDef(
                key="comms.nb.up.lastTxEpochMs",
                name="NB Up Last Tx",
                unit="ms",
                data_type="int",
                desc="NB uplink last TX timestamp",
                gen=lambda s: int(s.epoch_ms - random.randint(0, 300)),
            ),
            VarDef(
                key="comms.nb.up.lastRxEpochMs",
                name="NB Up Last Rx",
                unit="ms",
                data_type="int",
                desc="NB uplink last RX timestamp",
                gen=lambda s: int(s.epoch_ms - random.randint(50, 500)),
            ),
            # NB downlink
            VarDef(
                key="comms.nb.down.health",
                name="NB Down Health",
                unit=None,
                data_type="text",
                desc="NB downlink health",
                gen=lambda s: comms_health(q_nb_down(s)),
            ),
            VarDef(
                key="comms.nb.down.state",
                name="NB Down State",
                unit=None,
                data_type="text",
                desc="NB downlink state",
                gen=lambda s: comms_state(s.t(), 3.0),
            ),
            VarDef(
                key="comms.nb.down.rateBps",
                name="NB Down Rate",
                unit="b/s",
                data_type="num",
                desc="NB downlink rate",
                gen=lambda s: round(nb_down_rate(s), 0),
            ),
            VarDef(
                key="comms.nb.down.rateAvgBps",
                name="NB Down Rate Avg",
                unit="b/s",
                data_type="num",
                desc="NB downlink avg rate",
                gen=lambda s: round(90_000 + 120_000 * comms_quality(s.t(), 55.0, 2.0), 0),
            ),
            VarDef(
                key="comms.nb.down.utilPct",
                name="NB Down Util",
                unit="%",
                data_type="num",
                desc="NB downlink utilization",
                gen=lambda s: round(clamp(nb_down_rate(s) / 250_000 * 100.0, 0, 100), 1),
            ),
            VarDef(
                key="comms.nb.down.rsrpDbm",
                name="NB Down RSRP",
                unit="dBm",
                data_type="num",
                desc="NB downlink RSRP",
                gen=lambda s: round(-110.0 + 25.0 * q_nb_down(s) + random.gauss(0.0, 1.0), 1),
            ),
            VarDef(
                key="comms.nb.down.rsrqDb",
                name="NB Down RSRQ",
                unit="dB",
                data_type="num",
                desc="NB downlink RSRQ",
                gen=lambda s: round(-15.0 + 8.0 * q_nb_down(s) + random.gauss(0.0, 0.5), 1),
            ),
            VarDef(
                key="comms.nb.down.sinrDb",
                name="NB Down SINR",
                unit="dB",
                data_type="num",
                desc="NB downlink SINR",
                gen=lambda s: round(-2.0 + 12.0 * q_nb_down(s) + random.gauss(0.0, 0.4), 1),
            ),
            VarDef(
                key="comms.nb.down.rssiDbm",
                name="NB Down RSSI",
                unit="dBm",
                data_type="num",
                desc="NB downlink RSSI",
                gen=lambda s: round(-92.0 + 18.0 * q_nb_down(s) + random.gauss(0.0, 1.2), 1),
            ),
            VarDef(
                key="comms.nb.down.snrDb",
                name="NB Down SNR",
                unit="dB",
                data_type="num",
                desc="NB downlink SNR",
                gen=lambda s: round(2.0 + 9.0 * q_nb_down(s) + random.gauss(0.0, 0.3), 1),
            ),
            VarDef(
                key="comms.nb.down.ber",
                name="NB Down BER",
                unit=None,
                data_type="num",
                desc="NB downlink BER",
                gen=lambda s: round(max(1e-6, (1.0 - q_nb_down(s)) * 1.2e-3), 6),
            ),
            VarDef(
                key="comms.nb.down.per",
                name="NB Down PER",
                unit="%",
                data_type="num",
                desc="NB downlink PER",
                gen=lambda s: round((1.0 - q_nb_down(s)) * 3.0, 2),
            ),
            VarDef(
                key="comms.nb.down.packetLossPct",
                name="NB Down Packet Loss",
                unit="%",
                data_type="num",
                desc="NB downlink packet loss",
                gen=lambda s: round((1.0 - q_nb_down(s)) * 6.0, 2),
            ),
            VarDef(
                key="comms.nb.down.latencyMs",
                name="NB Down Latency",
                unit="ms",
                data_type="num",
                desc="NB downlink latency",
                gen=lambda s: round(140.0 + (1.0 - q_nb_down(s)) * 200.0, 0),
            ),
            VarDef(
                key="comms.nb.down.jitterMs",
                name="NB Down Jitter",
                unit="ms",
                data_type="num",
                desc="NB downlink jitter",
                gen=lambda s: round(8.0 + (1.0 - q_nb_down(s)) * 18.0, 0),
            ),
            VarDef(
                key="comms.nb.down.freqHz",
                name="NB Down Frequency",
                unit="Hz",
                data_type="num",
                desc="NB downlink center frequency",
                gen=lambda s: 433_920_000,
            ),
            VarDef(
                key="comms.nb.down.bandwidthHz",
                name="NB Down Bandwidth",
                unit="Hz",
                data_type="num",
                desc="NB downlink bandwidth",
                gen=lambda s: 125_000,
            ),
            VarDef(
                key="comms.nb.down.modcod",
                name="NB Down Mod/Cod",
                unit=None,
                data_type="text",
                desc="NB downlink modulation/coding",
                gen=lambda s: comms_modcod(q_nb_down(s)),
            ),
            VarDef(
                key="comms.nb.down.lastTxEpochMs",
                name="NB Down Last Tx",
                unit="ms",
                data_type="int",
                desc="NB downlink last TX timestamp",
                gen=lambda s: int(s.epoch_ms - random.randint(0, 500)),
            ),
            VarDef(
                key="comms.nb.down.lastRxEpochMs",
                name="NB Down Last Rx",
                unit="ms",
                data_type="int",
                desc="NB downlink last RX timestamp",
                gen=lambda s: int(s.epoch_ms - random.randint(0, 400)),
            ),
            # BB downlink
            VarDef(
                key="comms.bb.down.health",
                name="BB Down Health",
                unit=None,
                data_type="text",
                desc="BB downlink health",
                gen=lambda s: comms_health(q_bb_down(s)),
            ),
            VarDef(
                key="comms.bb.down.state",
                name="BB Down State",
                unit=None,
                data_type="text",
                desc="BB downlink state",
                gen=lambda s: comms_state(s.t(), 1.0),
            ),
            VarDef(
                key="comms.bb.down.rateBps",
                name="BB Down Rate",
                unit="b/s",
                data_type="num",
                desc="BB downlink rate",
                gen=lambda s: round(bb_down_rate(s), 0),
            ),
            VarDef(
                key="comms.bb.down.rateAvgBps",
                name="BB Down Rate Avg",
                unit="b/s",
                data_type="num",
                desc="BB downlink avg rate",
                gen=lambda s: round(3_500_000 + 2_200_000 * comms_quality(s.t(), 35.0, 1.0), 0),
            ),
            VarDef(
                key="comms.bb.down.utilPct",
                name="BB Down Util",
                unit="%",
                data_type="num",
                desc="BB downlink utilization",
                gen=lambda s: round(clamp(bb_down_rate(s) / 8_000_000 * 100.0, 0, 100), 1),
            ),
            VarDef(
                key="comms.bb.down.rssiDbm",
                name="BB Down RSSI",
                unit="dBm",
                data_type="num",
                desc="BB downlink RSSI",
                gen=lambda s: round(-70.0 + 10.0 * q_bb_down(s) + random.gauss(0.0, 1.0), 1),
            ),
            VarDef(
                key="comms.bb.down.snrDb",
                name="BB Down SNR",
                unit="dB",
                data_type="num",
                desc="BB downlink SNR",
                gen=lambda s: round(8.0 + 12.0 * q_bb_down(s) + random.gauss(0.0, 0.4), 1),
            ),
            VarDef(
                key="comms.bb.down.mcs",
                name="BB Down MCS",
                unit=None,
                data_type="int",
                desc="BB downlink MCS index",
                gen=lambda s: int(3 + 6 * q_bb_down(s)),
            ),
            VarDef(
                key="comms.bb.down.phyRateBps",
                name="BB Down PHY Rate",
                unit="b/s",
                data_type="num",
                desc="BB downlink PHY rate",
                gen=lambda s: round(bb_down_rate(s) * 1.3, 0),
            ),
            VarDef(
                key="comms.bb.down.per",
                name="BB Down PER",
                unit="%",
                data_type="num",
                desc="BB downlink PER",
                gen=lambda s: round((1.0 - q_bb_down(s)) * 1.5, 2),
            ),
            VarDef(
                key="comms.bb.down.packetLossPct",
                name="BB Down Packet Loss",
                unit="%",
                data_type="num",
                desc="BB downlink packet loss",
                gen=lambda s: round((1.0 - q_bb_down(s)) * 3.0, 2),
            ),
            VarDef(
                key="comms.bb.down.latencyMs",
                name="BB Down Latency",
                unit="ms",
                data_type="num",
                desc="BB downlink latency",
                gen=lambda s: round(40.0 + (1.0 - q_bb_down(s)) * 40.0, 0),
            ),
            VarDef(
                key="comms.bb.down.jitterMs",
                name="BB Down Jitter",
                unit="ms",
                data_type="num",
                desc="BB downlink jitter",
                gen=lambda s: round(2.0 + (1.0 - q_bb_down(s)) * 6.0, 0),
            ),
            VarDef(
                key="comms.bb.down.freqHz",
                name="BB Down Frequency",
                unit="Hz",
                data_type="num",
                desc="BB downlink center frequency",
                gen=lambda s: 5_800_000_000,
            ),
            VarDef(
                key="comms.bb.down.bandwidthHz",
                name="BB Down Bandwidth",
                unit="Hz",
                data_type="num",
                desc="BB downlink bandwidth",
                gen=lambda s: 20_000_000,
            ),
            VarDef(
                key="comms.bb.down.channel",
                name="BB Down Channel",
                unit=None,
                data_type="int",
                desc="BB downlink channel",
                gen=lambda s: 149,
            ),
            VarDef(
                key="comms.bb.down.lastTxEpochMs",
                name="BB Down Last Tx",
                unit="ms",
                data_type="int",
                desc="BB downlink last TX timestamp",
                gen=lambda s: int(s.epoch_ms - random.randint(0, 200)),
            ),
            VarDef(
                key="comms.bb.down.lastRxEpochMs",
                name="BB Down Last Rx",
                unit="ms",
                data_type="int",
                desc="BB downlink last RX timestamp",
                gen=lambda s: int(s.epoch_ms - random.randint(0, 200)),
            ),
        ]
    )

    # -----------------------------
    # Mission / cameras / radar / ground station
    # -----------------------------
    vars.extend(
        [
            VarDef(
                key="mission.vehicle",
                name="Mission Vehicle",
                unit=None,
                data_type="text",
                desc="Vehicle name",
                gen=lambda s: "Aerobär",
            ),
            VarDef(
                key="mission.phase",
                name="Mission Phase",
                unit=None,
                data_type="text",
                desc="Mission phase",
                gen=lambda s: "Pre-flight phase",
            ),
            VarDef(
                key="mission.pad",
                name="Mission Pad",
                unit=None,
                data_type="text",
                desc="Pad name",
                gen=lambda s: "Pad Station 1",
            ),
            VarDef(
                key="cameras.summary",
                name="Cameras Summary",
                unit=None,
                data_type="text",
                desc="Camera availability summary",
                gen=lambda s: "2/3",
            ),
            VarDef(
                key="cameras.ob1",
                name="Camera OB1",
                unit=None,
                data_type="text",
                desc="Camera OB1 status",
                gen=lambda s: "ok",
            ),
            VarDef(
                key="cameras.ob2",
                name="Camera OB2",
                unit=None,
                data_type="text",
                desc="Camera OB2 status",
                gen=lambda s: "ok",
            ),
            VarDef(
                key="cameras.pad",
                name="Camera Pad",
                unit=None,
                data_type="text",
                desc="Pad camera status",
                gen=lambda s: "error",
            ),
            VarDef(
                key="ground.station.status",
                name="Ground Station Status",
                unit=None,
                data_type="text",
                desc="Ground station status",
                gen=lambda s: "Operational",
            ),
            VarDef(
                key="ground.station.link",
                name="Ground Station Link",
                unit=None,
                data_type="text",
                desc="Ground station link",
                gen=lambda s: "Wi-Fi link",
            ),
            VarDef(
                key="radar.status",
                name="Radar Status",
                unit=None,
                data_type="text",
                desc="Radar status",
                gen=lambda s: "Locked-On",
            ),
            VarDef(
                key="radar.mode",
                name="Radar Mode",
                unit=None,
                data_type="text",
                desc="Radar mode",
                gen=lambda s: "IR",
            ),
        ]
    )

    return vars


def to_measurement_row(
    ts: int,
    sensor_id: int,
    variable_id: int,
    value_type: str,
    value: Any,
) -> Tuple[int, int, int, str, Optional[float], Optional[int], Optional[int], Optional[str], Optional[str], Optional[bytes]]:
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

    pending_rows: List[Tuple[int, int, int, str, Optional[float], Optional[int], Optional[int], Optional[str], Optional[str], Optional[bytes]]] = []

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

        ts = unix_ms()

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
