import base64
import datetime
import hashlib
import hmac
import os
from typing import Dict, List, Optional, Tuple

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
