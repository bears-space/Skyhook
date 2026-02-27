import os
import time
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def ensure_schema():
    host = _env("DB_HOST", "db")
    port = int(_env("DB_PORT", "3306"))
    user = _env("DB_USER", "skyhook")
    password = _env("DB_PASS", "skyhookpass")
    database = _env("DB_NAME", "skyhook")

    sql_path = Path(__file__).with_name("schema.sql")
    sql = sql_path.read_text(encoding="utf-8")

    # Wait for DB to accept connections (compose healthcheck should handle this,
    # but this makes local runs more robust).
    last_err = None
    for _ in range(10):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                autocommit=True,
                client_flag=CLIENT.MULTI_STATEMENTS,
            )
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    while cur.nextset():
                        pass
                return
            finally:
                conn.close()
                print("[init_db] DB schema ensured")
        except Exception as e:
            last_err = e
            time.sleep(0.1)

    raise RuntimeError(f"DB not ready / schema init failed: {last_err}")
