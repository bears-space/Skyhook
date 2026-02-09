import base64
import datetime
import hashlib
import hmac
import os
from typing import Dict, Iterable, List, Optional, Tuple

import jwt
import pymysql
from pymysql.err import OperationalError

from database.cdc_bridge import DBConfig

# Password hashing helpers -----------------------------------------------------

def _pbkdf2_hash(password: str, salt: bytes, iterations: int = 240_000) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str, iterations: int = 240_000, salt_bytes: int = 16) -> str:
    salt = os.urandom(salt_bytes)
    digest = _pbkdf2_hash(password, salt, iterations)
    return "pbkdf2_sha256$%d$%s$%s" % (
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored or "$" not in stored:
        return False
    try:
        method, iter_str, salt_b64, hash_b64 = stored.split("$")
        if method != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        candidate = _pbkdf2_hash(password, salt, iterations)
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


# DB helpers -------------------------------------------------------------------

def _db_conn(cfg: DBConfig) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def _ensure_auth_columns(cfg: DBConfig) -> None:
    """Add missing auth columns on legacy databases."""
    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            # users.email
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='email'
                """,
                (cfg.database,),
            )
            if int(cur.fetchone().get("n", 0)) == 0:
                cur.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL AFTER username")

            # users.password_hash
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='password_hash'
                """,
                (cfg.database,),
            )
            if int(cur.fetchone().get("n", 0)) == 0:
                cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL AFTER email")

            # users.is_active
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='is_active'
                """,
                (cfg.database,),
            )
            if int(cur.fetchone().get("n", 0)) == 0:
                cur.execute("ALTER TABLE users ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER password_hash")

            # users.created_at
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='created_at'
                """,
                (cfg.database,),
            )
            if int(cur.fetchone().get("n", 0)) == 0:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER is_active"
                )

            # users.updated_at
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='updated_at'
                """,
                (cfg.database,),
            )
            if int(cur.fetchone().get("n", 0)) == 0:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at"
                )
    finally:
        conn.close()


def _user_count(cfg: DBConfig) -> int:
    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM users")
            row = cur.fetchone()
            return int(row["n"]) if row else 0
    finally:
        conn.close()


def _fetch_user(cfg: DBConfig, identifier: str) -> Optional[Dict]:
    sql = """SELECT id, username, email, password_hash, is_active
             FROM users
             WHERE username=%s OR email=%s
             LIMIT 1"""
    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (identifier, identifier))
            return cur.fetchone()
    except OperationalError as exc:
        # Legacy schema missing columns: fix and retry once
        if exc.args and exc.args[0] == 1054:
            _ensure_auth_columns(cfg)
            with conn.cursor() as cur:
                cur.execute(sql, (identifier, identifier))
                return cur.fetchone()
        raise
    finally:
        conn.close()


def _fetch_roles(cfg: DBConfig, user_id: int) -> List[str]:
    sql = """SELECT r.name
             FROM user_roles ur
             JOIN roles r ON r.id = ur.role_id
             WHERE ur.user_id=%s"""
    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            return [row["name"] for row in cur.fetchall()]
    finally:
        conn.close()


# Auth API ---------------------------------------------------------------------

def verify_credentials(cfg: DBConfig, identifier: str, password: str) -> Tuple[Optional[Dict], Optional[List[str]]]:
    user = _fetch_user(cfg, identifier)
    if not user or not user.get("is_active"):
        # Bootstrap path: if no users exist, allow default admin login
        if _user_count(cfg) == 0:
            default_user = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@local")
            default_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "letmein")
            if identifier in (default_user, default_email) and password == default_pass:
                bootstrap_user = {
                    "id": "bootstrap-admin",
                    "username": default_user,
                    "email": default_email,
                    "is_active": 1,
                }
                return bootstrap_user, ["admin"]
        return None, None

    if not verify_password(password, user.get("password_hash")):
        return None, None

    roles = _fetch_roles(cfg, int(user["id"]))
    return user, roles


def generate_jwt(secret: str, ttl_seconds: int, user: Dict, roles: List[str]) -> str:
    now = datetime.datetime.utcnow()
    exp = now + datetime.timedelta(seconds=ttl_seconds)
    payload = {
        "sub": str(user["id"]),
        "email": user.get("email"),
        "username": user.get("username"),
        "roles": roles,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str) -> Dict:
    return jwt.decode(token, secret, algorithms=["HS256"])


# User management helpers ------------------------------------------------------

def _ensure_roles(conn: pymysql.connections.Connection, role_names: Iterable[str]) -> List[int]:
    """
    Ensure roles exist and return their IDs.
    """
    names = [r.strip().lower() for r in role_names if r and str(r).strip()]
    if not names:
        return []

    role_ids: List[int] = []
    with conn.cursor() as cur:
        for name in names:
            cur.execute(
                "INSERT INTO roles (name) VALUES (%s) ON DUPLICATE KEY UPDATE name=name",
                (name,),
            )

        placeholders = ",".join(["%s"] * len(names))
        cur.execute(f"SELECT id, name FROM roles WHERE name IN ({placeholders})", names)
        rows = cur.fetchall()
        role_ids = [int(r["id"]) for r in rows]
    return role_ids


def _load_user_with_roles(conn: pymysql.connections.Connection, user_id: int, cfg: DBConfig) -> Optional[Dict]:
    sql = """
        SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.updated_at,
               GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ',') AS roles
        FROM users u
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE u.id = %s
        GROUP BY u.id
        LIMIT 1
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            roles = row.get("roles") or ""
            return {
                "id": int(row["id"]),
                "username": row.get("username"),
                "email": row.get("email"),
                "is_active": bool(row.get("is_active")),
                "roles": [r for r in roles.split(",") if r],
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
    except OperationalError as exc:
        if exc.args and exc.args[0] == 1054:
            _ensure_auth_columns(cfg)
            return _load_user_with_roles(conn, user_id, cfg)
        raise


def list_users(cfg: DBConfig) -> List[Dict]:
    """
    Return all users with roles; omits password hashes.
    """
    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.updated_at,
                       GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ',') AS roles
                FROM users u
                LEFT JOIN user_roles ur ON ur.user_id = u.id
                LEFT JOIN roles r ON r.id = ur.role_id
                GROUP BY u.id
                ORDER BY u.id ASC
            """
            try:
                cur.execute(sql)
            except OperationalError as exc:
                if exc.args and exc.args[0] == 1054:
                    _ensure_auth_columns(cfg)
                    cur.execute(sql)
                else:
                    raise
            rows = cur.fetchall()
            out = []
            for row in rows:
                roles = row.get("roles") or ""
                out.append(
                    {
                        "id": int(row["id"]),
                        "username": row.get("username"),
                        "email": row.get("email"),
                        "is_active": bool(row.get("is_active")),
                        "roles": [r for r in roles.split(",") if r],
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at"),
                    }
                )
            return out
    finally:
        conn.close()


def create_user(
    cfg: DBConfig,
    username: str,
    email: Optional[str],
    password: str,
    roles: Optional[List[str]] = None,
    is_active: bool = True,
) -> Dict:
    """
    Create a user with hashed password and assigned roles.
    """
    if not username:
        raise ValueError("username is required")
    if not password:
        raise ValueError("password is required")

    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, is_active)
                VALUES (%s, %s, %s, %s)
                """,
                (username, email, hash_password(password), 1 if is_active else 0),
            )
            user_id = int(cur.lastrowid)

            role_ids = _ensure_roles(conn, roles or [])
            for rid in role_ids:
                cur.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, rid),
                )

        try:
            return _load_user_with_roles(conn, user_id, cfg)  # type: ignore[arg-type]
        except OperationalError as exc:
            if exc.args and exc.args[0] == 1054:
                _ensure_auth_columns(cfg)
                return _load_user_with_roles(conn, user_id, cfg)
            raise
    finally:
        conn.close()


def update_user(
    cfg: DBConfig,
    user_id: int,
    *,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    roles: Optional[List[str]] = None,
    is_active: Optional[bool] = None,
) -> Optional[Dict]:
    """
    Update user fields and role assignments. Returns updated user or None if not found.
    """
    conn = _db_conn(cfg)
    try:
        sets = []
        params: List = []

        if username is not None:
            sets.append("username=%s")
            params.append(username)
        if email is not None:
            sets.append("email=%s")
            params.append(email)
        if password is not None:
            sets.append("password_hash=%s")
            params.append(hash_password(password))
        if is_active is not None:
            sets.append("is_active=%s")
            params.append(1 if is_active else 0)

        if sets:
            sql = f"UPDATE users SET {', '.join(sets)} WHERE id=%s"
            params.append(user_id)
            with conn.cursor() as cur:
                try:
                    cur.execute(sql, params)
                except OperationalError as exc:
                    if exc.args and exc.args[0] == 1054:
                        _ensure_auth_columns(cfg)
                        cur.execute(sql, params)
                    else:
                        raise

        if roles is not None:
            role_ids = _ensure_roles(conn, roles)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_roles WHERE user_id=%s", (user_id,))
                for rid in role_ids:
                    cur.execute(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                        (user_id, rid),
                    )

        try:
            return _load_user_with_roles(conn, user_id, cfg)
        except OperationalError as exc:
            if exc.args and exc.args[0] == 1054:
                _ensure_auth_columns(cfg)
                return _load_user_with_roles(conn, user_id, cfg)
            raise
    finally:
        conn.close()


def delete_user(cfg: DBConfig, user_id: int) -> bool:
    conn = _db_conn(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            return cur.rowcount > 0
    finally:
        conn.close()
