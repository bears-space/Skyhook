from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room, ConnectionRefusedError
from flask_cors import CORS
import jwt
import datetime
from jwt import InvalidTokenError

from init_db import ensure_schema
from database.cdc_bridge import (
    DBConfig,
    CDCConfig,
    CDCBridge,
    get_latest_snapshot,
    get_sensor_ids,
    room_for_sensor,
)

ensure_schema()

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["JWT_SECRET"] = "skyhook-dev-secret"  # replace in production
app.config["JWT_TTL_SECONDS"] = 60 * 60  # 1 hour

# Allow API usage from the Vite dev server and elsewhere; tighten origins for prod
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Wichtig: threading ist für Background-Threads am unkompliziertesten im Dev
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db_cfg = DBConfig()
cdc_cfg = CDCConfig()

if cdc_cfg.enabled:
    CDCBridge(socketio, db_cfg, cdc_cfg).start()


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Very basic demo login that checks hardcoded credentials and returns a JWT."""
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    #TODO: Hardcoded demo creds; replace with real user lookup.
    if email != "admin@skyhook.local" or password != "letmein":
        return jsonify({"error": "Invalid credentials"}), 401

    now = datetime.datetime.utcnow()
    exp = now + datetime.timedelta(seconds=app.config["JWT_TTL_SECONDS"])
    token = jwt.encode(
        {"sub": email, "iat": now, "exp": exp},
        app.config["JWT_SECRET"],
        algorithm="HS256",
    )

    return jsonify({"token": token, "user": {"email": email}})


@socketio.on("connect")
def handle_connect(auth):
    """Require a valid JWT in the connection auth payload or query string."""
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")

    # Fallback: allow token via query string ?token=... for compatibility
    if not token:
        token = request.args.get("token")

    if not token:
        print("Socket connect refused: missing token")
        raise ConnectionRefusedError("Missing token")

    try:
        claims = jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
    except InvalidTokenError as exc:
        print(f"Socket connect refused: invalid token ({exc})")
        raise ConnectionRefusedError("Invalid token")

    # Stash identity on the request context for later use (rooms, logging, etc.)
    request.environ["skyhook_user"] = claims.get("sub", "unknown")
    print(f"Socket client connected as {request.environ['skyhook_user']}")
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


@socketio.on("subscribe_all")
def handle_subscribe_all(data=None):
    """
    data (optional):
      { "variable_ids": [1,2,3] }  # variable_ids optional
    """
    variable_ids = None
    if isinstance(data, dict):
        variable_ids = data.get("variable_ids")
        if variable_ids is not None:
            variable_ids = [int(x) for x in variable_ids]

    sensor_ids = get_sensor_ids(db_cfg)
    for sensor_id in sensor_ids:
        room = room_for_sensor(sensor_id)
        join_room(room)
        snap = get_latest_snapshot(db_cfg, sensor_id, variable_ids=variable_ids)
        emit("snapshot", snap)

    emit("subscribed_all", {"sensors": sensor_ids})


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
