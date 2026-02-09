# skyhook-backend/cdc_bridge.py

from __future__ import annotations

import json
import os
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pymysql
from pymysql.constants import CLIENT

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import WriteRowsEvent, UpdateRowsEvent


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class DBConfig:
    host: str = _env("DB_HOST", "db")
    port: int = int(_env("DB_PORT", "3306"))
    user: str = _env("DB_USER", "skyhook")
    password: str = _env("DB_PASS", "skyhookpass")
    database: str = _env("DB_NAME", "skyhook")


@dataclass(frozen=True)
class CDCConfig:
    enabled: bool = _env("CDC_ENABLED", "1") == "1"
    cdc_user: str = _env("CDC_DB_USER", "cdc_user")
    cdc_pass: str = _env("CDC_DB_PASS", "cdc_pass")
    server_id: int = int(_env("CDC_SERVER_ID", "1337"))
    batch_ms: int = int(_env("CDC_BATCH_MS", "100"))
    queue_max: int = int(_env("CDC_QUEUE_MAX", "10000"))


def room_for_sensor(sensor_id: int) -> str:
    return f"sensor:{sensor_id}"


def _db_conn_read(cfg: DBConfig) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )


def _normalize_row_keys(values: Dict[str, Any]) -> Dict[str, Any]:
    """
    If binlog_row_metadata != FULL, you may see UNKNOWN_COL0..N.
    Map by fixed column order for measurements to keep things robust.
    """
    if "UNKNOWN_COL0" not in values:
        return values

    # measurements columns in order:
    # id, ts, sensor_id, variable_id, value_type, value_num, value_int, value_bool, value_text, value_json, value_blob
    keys = [
        "id",
        "ts",
        "sensor_id",
        "variable_id",
        "value_type",
        "value_num",
        "value_int",
        "value_bool",
        "value_text",
        "value_json",
        "value_blob",
    ]
    out: Dict[str, Any] = {}
    for i, k in enumerate(keys):
        out[k] = values.get(f"UNKNOWN_COL{i}")
    return out


def _decode_value_from_row(row: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    """
    Decode (value_type, value) from a measurements row.
    Works both with proper metadata and with fallback inference.
    """
    vt = row.get("value_type")

    if isinstance(vt, str) and vt:
        if vt == "num":
            return vt, row.get("value_num")
        if vt == "int":
            return vt, row.get("value_int")
        if vt == "bool":
            v = row.get("value_bool")
            return vt, bool(v) if v is not None else None
        if vt == "text":
            return vt, row.get("value_text")
        if vt == "json":
            raw = row.get("value_json")
            if raw is None:
                return vt, None
            try:
                return vt, json.loads(raw)
            except Exception:
                return vt, raw
        if vt == "blob":
            return vt, None

    # Fallback: infer from first non-null typed column
    for k, t in [
        ("value_num", "num"),
        ("value_int", "int"),
        ("value_bool", "bool"),
        ("value_text", "text"),
        ("value_json", "json"),
        ("value_blob", "blob"),
    ]:
        if row.get(k) is not None:
            if t == "bool":
                return t, bool(row.get(k))
            if t == "json":
                raw = row.get(k)
                try:
                    return t, json.loads(raw)
                except Exception:
                    return t, raw
            if t == "blob":
                return t, None
            return t, row.get(k)

    return None, None


def _ts_to_ms(ts_val: Any) -> int:
    if isinstance(ts_val, datetime):
        return int(ts_val.replace(tzinfo=timezone.utc).timestamp() * 1000)
    if isinstance(ts_val, (int, float)):
        return int(ts_val)
    try:
        return int(ts_val)
    except Exception:
        return 0


def _load_variable_key_map(db_cfg: DBConfig) -> Dict[int, str]:
    conn = _db_conn_read(db_cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, `key` FROM variables")
            rows = cur.fetchall()
            return {int(r[0]): str(r[1]) for r in rows}
    finally:
        conn.close()


def get_latest_snapshot(
    db_cfg: DBConfig,
    sensor_id: int,
    variable_ids: Optional[List[int]] = None,
    limit_scan: int = 500,
) -> Dict[str, Any]:
    """
    Snapshot for UI: latest value per variable_id for one sensor.
    Dev-friendly approach: scan last N rows and reduce in Python.
    """
    params: List[Any] = [sensor_id]

    if variable_ids:
        placeholders = ",".join(["%s"] * len(variable_ids))
        q = f"""
            SELECT m.id, m.ts, m.sensor_id, m.variable_id, v.`key` AS variable_key, m.value_type,
                   m.value_num, m.value_int, m.value_bool, m.value_text, m.value_json, m.value_blob
            FROM measurements m
            JOIN variables v ON v.id = m.variable_id
            WHERE m.sensor_id = %s AND m.variable_id IN ({placeholders})
            ORDER BY m.ts DESC
            LIMIT %s
        """
        params.extend([int(x) for x in variable_ids])
        params.append(limit_scan)
    else:
        q = """
            SELECT m.id, m.ts, m.sensor_id, m.variable_id, v.`key` AS variable_key, m.value_type,
                   m.value_num, m.value_int, m.value_bool, m.value_text, m.value_json, m.value_blob
            FROM measurements m
            JOIN variables v ON v.id = m.variable_id
            WHERE m.sensor_id = %s
            ORDER BY m.ts DESC
            LIMIT %s
        """
        params.append(limit_scan)

    latest: Dict[int, Dict[str, Any]] = {}

    conn = _db_conn_read(db_cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            for r in rows:
                row = dict(zip(cols, r))
                vid = int(row["variable_id"])
                if vid in latest:
                    continue

                vt, v = _decode_value_from_row(row)
                ts_ms = _ts_to_ms(row.get("ts"))

                latest[vid] = {
                    "id": row.get("id"),
                    "ts": ts_ms,
                    "sensor_id": int(row.get("sensor_id")),
                    "variable_id": vid,
                    "variable_key": row.get("variable_key"),
                    "value_type": vt,
                    "value": v,
                }
    finally:
        conn.close()

    return {"sensor_id": sensor_id, "latest": list(latest.values())}


def get_sensor_ids(db_cfg: DBConfig) -> List[int]:
    conn = _db_conn_read(db_cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sensors ORDER BY id ASC")
            rows = cur.fetchall()
            return [int(r[0]) for r in rows]
    finally:
        conn.close()


class CDCBridge:
    """
    CDC Bridge: MariaDB binlog -> in-memory queue -> Socket.IO room emits.

    Emits:
      event "measurements": {"sensor_id": <id>, "items": [<measurement_payload>...]}
    """

    def __init__(self, socketio, db_cfg: DBConfig, cdc_cfg: CDCConfig):
        self.socketio = socketio
        self.db_cfg = db_cfg
        self.cdc_cfg = cdc_cfg

        self._stop = threading.Event()
        self._started = False
        self._start_lock = threading.Lock()

        self._queue: List[Dict[str, Any]] = []
        self._queue_lock = threading.Lock()

        self._reader_thread: Optional[threading.Thread] = None
        self._var_key_cache: Dict[int, str] = _load_variable_key_map(db_cfg)
        self._var_key_lock = threading.Lock()

    def start(self) -> None:
        with self._start_lock:
            if self._started:
                return
            self._started = True

        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

        # run flush loop via SocketIO background task (thread-safe emits)
        self.socketio.start_background_task(self._flush_loop)

        print("[cdc] CDCBridge started ✅")

    def stop(self) -> None:
        self._stop.set()

    def _enqueue(self, payload: Dict[str, Any]) -> None:
        with self._queue_lock:
            if len(self._queue) >= self.cdc_cfg.queue_max:
                # Latest-wins behavior for dev
                self._queue = self._queue[-(self.cdc_cfg.queue_max // 2) :]
            self._queue.append(payload)

    def _drain(self) -> List[Dict[str, Any]]:
        with self._queue_lock:
            batch = self._queue
            self._queue = []
            return batch

    def _to_payload(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sensor_id = row.get("sensor_id")
        variable_id = row.get("variable_id")
        if sensor_id is None or variable_id is None:
            return None

        vt, v = _decode_value_from_row(row)
        variable_key = None
        try:
            variable_key = self._var_key_cache.get(int(variable_id))
            if variable_key is None:
                with self._var_key_lock:
                    variable_key = self._var_key_cache.get(int(variable_id))
                    if variable_key is None:
                        self._var_key_cache = _load_variable_key_map(self.db_cfg)
                        variable_key = self._var_key_cache.get(int(variable_id))
        except Exception:
            variable_key = None

        ts_ms = _ts_to_ms(row.get("ts"))

        return {
            "id": row.get("id"),
            "ts": ts_ms,
            "sensor_id": int(sensor_id),
            "variable_id": int(variable_id),
            "variable_key": variable_key,
            "value_type": vt,
            "value": v,
        }

    def _reader_loop(self) -> None:
        """
        Binlog reader thread. Reconnects on errors.
        """
        while not self._stop.is_set():
            stream = None
            try:
                stream = BinLogStreamReader(
                    connection_settings=dict(
                        host=self.db_cfg.host,
                        port=self.db_cfg.port,
                        user=self.cdc_cfg.cdc_user,
                        passwd=self.cdc_cfg.cdc_pass,
                    ),
                    server_id=self.cdc_cfg.server_id,
                    blocking=True,
                    resume_stream=True,
                    only_schemas=[self.db_cfg.database],
                    only_tables=["measurements"],
                    only_events=[WriteRowsEvent, UpdateRowsEvent],
                )

                print("[cdc] binlog stream connected")

                for event in stream:
                    if self._stop.is_set():
                        break

                    if isinstance(event, WriteRowsEvent):
                        for row in event.rows:
                            values = _normalize_row_keys(row["values"])
                            payload = self._to_payload(values)
                            if payload:
                                self._enqueue(payload)

                    elif isinstance(event, UpdateRowsEvent):
                        for row in event.rows:
                            values = _normalize_row_keys(row["after_values"])
                            payload = self._to_payload(values)
                            if payload:
                                self._enqueue(payload)

            except Exception as e:
                print(f"[cdc] stream error: {e} (reconnect in 0.5s)")
                time.sleep(0.5)
            finally:
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass

    def _flush_loop(self) -> None:
        """
        Flush batched messages every batch_ms.
        Emits grouped by sensor room.
        """
        while not self._stop.is_set():
            time.sleep(self.cdc_cfg.batch_ms / 1000.0)

            batch = self._drain()
            if not batch:
                continue

            grouped: Dict[int, List[Dict[str, Any]]] = {}
            for item in batch:
                grouped.setdefault(item["sensor_id"], []).append(item)

            for sensor_id, items in grouped.items():
                print(f"[cdc] emitting {len(items)} items for sensor {sensor_id}")
                try:
                    self.socketio.emit(
                        "measurements",
                        {"sensor_id": sensor_id, "items": items},
                        room=room_for_sensor(sensor_id),
                    )
                except Exception as e:
                    print(f"[cdc] emit error for sensor {sensor_id}: {e}")
