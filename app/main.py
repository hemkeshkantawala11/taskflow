"""TaskFlow - a small shared task list, instrumented for operation on Kubernetes.

Endpoints
  /                 web UI
  /api/tasks        task CRUD (the user-facing API; this is what the SLO measures)
  /healthz          liveness: is the process able to serve at all?
  /readyz           readiness: can this pod serve real requests (DB reachable)?
  /version          which build is running (traceability back to the git commit)
  /metrics          Prometheus metrics
"""

import logging
import random
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from . import db
from .config import settings
from .observability import (
    DB_UP,
    TASKS_CREATED,
    MetricsMiddleware,
    setup_logging,
    setup_tracing,
)

STATIC_DIR = Path(__file__).parent / "static"

setup_logging()
log = logging.getLogger("taskflow")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.open_pool()
    db.ensure_schema()  # best effort; readiness keeps retrying if the DB isn't up yet
    log.info("taskflow started version=%s git_sha=%s", settings.app_version, settings.git_sha)
    yield
    log.info("taskflow shutting down")
    db.close_pool()


app = FastAPI(title="TaskFlow", version=settings.app_version, lifespan=lifespan)
setup_tracing(app)


def inject_chaos():
    """Deliberate fault injection for the alerting/recovery demo (off by default).

    A route dependency, not middleware: it runs after routing, so injected failures are
    counted under the real route template and the /api SLO sees them.
    """
    if settings.chaos_error_rate > 0 and random.random() < settings.chaos_error_rate:
        raise HTTPException(status_code=500, detail="Injected failure (CHAOS_ERROR_RATE)")


API_DEPS = [Depends(inject_chaos)]


# Outermost middleware, so it also measures failures raised by routes and dependencies.
app.add_middleware(MetricsMiddleware)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskPatch(BaseModel):
    done: bool


# ---------------------------------------------------------------- operational endpoints
@app.get("/healthz", include_in_schema=False)
def healthz():
    # Liveness deliberately does NOT check the database: if Postgres is down,
    # restarting every app pod would not fix anything and would only add churn.
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
def readyz():
    ok = db.ping()
    DB_UP.set(1 if ok else 0)
    if not ok:
        return JSONResponse({"status": "not ready", "database": "unreachable"}, status_code=503)
    return {"status": "ready", "database": "ok"}


@app.get("/version")
def version():
    return {
        "version": settings.app_version,
        "git_sha": settings.git_sha,
        "build_time": settings.build_time,
        "pod": settings.pod_name,
    }


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------- application
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/tasks", dependencies=API_DEPS)
def list_tasks(limit: int = Query(100, ge=1, le=500)):
    # Bounded: an unbounded list grew to 2.3 MB per response under load testing.
    with db.pool.connection() as conn:
        return conn.execute(
            "SELECT id, title, done, created_at FROM tasks ORDER BY done, id DESC LIMIT %s",
            (limit,),
        ).fetchall()


@app.post("/api/tasks", status_code=201, dependencies=API_DEPS)
def create_task(task: TaskIn):
    with db.pool.connection() as conn:
        row = conn.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done, created_at",
            (task.title.strip(),),
        ).fetchone()
    TASKS_CREATED.inc()
    return row


@app.patch("/api/tasks/{task_id}", dependencies=API_DEPS)
def update_task(task_id: int, patch: TaskPatch):
    with db.pool.connection() as conn:
        row = conn.execute(
            "UPDATE tasks SET done = %s WHERE id = %s RETURNING id, title, done, created_at",
            (patch.done, task_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.delete("/api/tasks/{task_id}", status_code=204, dependencies=API_DEPS)
def delete_task(task_id: int):
    with db.pool.connection() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
