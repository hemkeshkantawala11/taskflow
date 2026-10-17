"""Database access: one connection pool per process.

Design notes (useful for the viva):
- A pool avoids opening a new TCP + auth handshake to Postgres on every request.
- The pool opens in the background (wait=False), so the app process starts even
  when Postgres is not up yet. Readiness stays false until the DB answers, so
  Kubernetes simply doesn't send traffic yet - no crash loops.
- Schema creation takes a Postgres advisory lock, so several replicas starting
  at the same time cannot race each other on CREATE TABLE.
"""

import logging
import threading

from opentelemetry.instrumentation.utils import suppress_instrumentation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

log = logging.getLogger("taskflow.db")

SCHEMA_LOCK_ID = 727_001  # arbitrary constant shared by all replicas

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS tasks_done_idx ON tasks (done);
"""

pool: ConnectionPool | None = None
_schema_ready = False
_schema_lock = threading.Lock()


def open_pool() -> ConnectionPool:
    global pool
    pool = ConnectionPool(
        conninfo=settings.conninfo,
        min_size=1,
        max_size=settings.db_pool_max,
        timeout=settings.db_timeout_seconds,
        kwargs={"row_factory": dict_row},
        open=False,
        name="taskflow",
    )
    pool.open(wait=False)
    return pool


def close_pool() -> None:
    if pool is not None:
        pool.close()


def ensure_schema() -> bool:
    """Create the schema once per process. Returns True when the schema exists."""
    global _schema_ready
    if _schema_ready:
        return True
    with _schema_lock:
        if _schema_ready:
            return True
        try:
            with pool.connection() as conn:
                with conn.transaction():
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (SCHEMA_LOCK_ID,))
                    conn.execute(SCHEMA_SQL)
            _schema_ready = True
            log.info("database schema ready")
        except Exception as exc:  # noqa: BLE001 - we log and retry on next readiness probe
            log.warning("schema not ready yet: %s", exc)
        return _schema_ready


def ping() -> bool:
    """Readiness check: can we run a trivial query within the timeout?

    Not traced: /readyz runs every few seconds per pod, and each SELECT 1 would
    become its own one-span trace, burying real user requests in Jaeger.
    """
    try:
        with suppress_instrumentation():
            with pool.connection(timeout=settings.db_timeout_seconds) as conn:
                conn.execute("SELECT 1")
            return ensure_schema()
    except Exception as exc:  # noqa: BLE001
        log.warning("database ping failed: %s", exc)
        return False
