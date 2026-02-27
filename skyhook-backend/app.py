from functools import wraps

from flask import Flask, jsonify, request, g
from flask_socketio import SocketIO, emit, join_room, leave_room, ConnectionRefusedError
from flask_cors import CORS
from jwt import InvalidTokenError
from pymysql.err import OperationalError

from auth_service import (
    verify_credentials,
    generate_jwt,
    decode_jwt,
    list_users,
    create_user,
    update_user,
    delete_user,
)

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


def _get_bearer_token() -> str:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return ""


def require_auth(admin: bool = False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = _get_bearer_token()
            if not token:
                return jsonify({"error": "Missing bearer token"}), 401
            try:
                claims = decode_jwt(token, app.config["JWT_SECRET"])
            except InvalidTokenError as exc:
                return jsonify({"error": f"Invalid token: {exc}"}), 401

            roles = claims.get("roles", []) or []
            if admin and "admin" not in roles:
                return jsonify({"error": "Admin role required"}), 403

            g.jwt_claims = claims
            g.jwt_token = token
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/api/auth/login", methods=["POST"])
def api_login():
  """Authenticate against database users and return a JWT with roles."""
  payload = request.get_json(silent=True) or {}
  identifier = (payload.get("email") or payload.get("username") or "").strip()
  password = payload.get("password") or ""

  user, roles = verify_credentials(db_cfg, identifier, password)
  if not user:
      return jsonify({"error": "Invalid credentials"}), 401

  token = generate_jwt(app.config["JWT_SECRET"], app.config["JWT_TTL_SECONDS"], user, roles or [])

  return jsonify({
      "token": token,
      "user": {
          "id": user["id"],
          "username": user["username"],
          "email": user.get("email"),
          "roles": roles or [],
      },
  })


@app.route("/api/users", methods=["GET"])
@require_auth(admin=True)
def api_users_list():
    users = list_users(db_cfg)
    return jsonify({"users": users})


@app.route("/api/users", methods=["POST"])
@require_auth(admin=True)
def api_users_create():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip() or None
    password = payload.get("password") or ""
    roles = payload.get("roles") or []
    is_active = bool(payload.get("is_active", True))

    try:
        user = create_user(db_cfg, username=username, email=email, password=password, roles=roles, is_active=is_active)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except OperationalError as exc:
        if exc.args and exc.args[0] == 1062:
            return jsonify({"error": "User with that username or email already exists"}), 409
        raise

    return jsonify({"user": user}), 201


@app.route("/api/users/<int:user_id>", methods=["PATCH"])
@require_auth(admin=True)
def api_users_update(user_id: int):
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    roles = payload.get("roles")
    is_active = payload.get("is_active")
    if is_active is not None:
        is_active = bool(is_active)

    try:
        user = update_user(
            db_cfg,
            user_id,
            username=username,
            email=email,
            password=password,
            roles=roles,
            is_active=is_active,
        )
    except OperationalError as exc:
        if exc.args and exc.args[0] == 1062:
            return jsonify({"error": "User with that username or email already exists"}), 409
        raise

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user})


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@require_auth(admin=True)
def api_users_delete(user_id: int):
    deleted = delete_user(db_cfg, user_id)
    if not deleted:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"status": "deleted"})


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
        claims = decode_jwt(token, app.config["JWT_SECRET"])
    except InvalidTokenError as exc:
        print(f"Socket connect refused: invalid token ({exc})")
        raise ConnectionRefusedError("Invalid token")

    # Stash identity on the request context for later use (rooms, logging, etc.)
    request.environ["skyhook_user"] = claims.get("sub", "unknown")
    request.environ["skyhook_roles"] = claims.get("roles", [])
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

