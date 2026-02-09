from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room

from init_db import ensure_schema
from database.cdc_bridge import (
    DBConfig,
    CDCConfig,
    CDCBridge,
    get_latest_snapshot,
    room_for_sensor,
)

ensure_schema()

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

# Wichtig: threading ist für Background-Threads am unkompliziertesten im Dev
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db_cfg = DBConfig()
cdc_cfg = CDCConfig()

if cdc_cfg.enabled:
    CDCBridge(socketio, db_cfg, cdc_cfg).start()


@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("message", {"data": "Connected to backend"})


@socketio.on("ping")
def handle_ping(data):
    emit("pong", {"data": data})


@socketio.on("subscribe")
def handle_subscribe(data):
    print(f"Client subscribe: {data}")
    """
    data:
      { "sensor_id": 1, "variable_ids": [1,2,3] }  # variable_ids optional
    """
    sensor_id = int(data["sensor_id"])
    variable_ids = data.get("variable_ids")
    if variable_ids is not None:
        variable_ids = [int(x) for x in variable_ids]

    room = room_for_sensor(sensor_id)
    join_room(room)

    # Snapshot sofort schicken (UI bekommt initial state)
    snap = get_latest_snapshot(db_cfg, sensor_id, variable_ids=variable_ids)
    emit("snapshot", snap)

    emit("subscribed", {"room": room})


@socketio.on("unsubscribe")
def handle_unsubscribe(data):
    sensor_id = int(data["sensor_id"])
    room = room_for_sensor(sensor_id)
    leave_room(room)
    emit("unsubscribed", {"room": room})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3000)

'''
WICHTIG: Dieses SQL-Statement muss einmalig in deiner MySQL/MariaDB ausgeführt werden, damit die CDC-Funktionalität korrekt funktioniert.

-- als root (oder User mit GRANT OPTION) ausführen

CREATE USER IF NOT EXISTS 'cdc_user'@'%' IDENTIFIED BY 'cdc_pass';

-- Rechte für Binlog/CDC:
GRANT REPLICATION SLAVE, REPLICATION CLIENT, BINLOG MONITOR ON *.* TO 'cdc_user'@'%';

-- Read access auf deine DB (Snapshot queries, Lookups, etc.)
GRANT SELECT ON `skyhook`.* TO 'cdc_user'@'%';

FLUSH PRIVILEGES;

-- Optional: check
SHOW GRANTS FOR 'cdc_user'@'%';
'''