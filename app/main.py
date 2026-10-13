"""TaskFlow - a small shared task list.

Run locally:
    export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/taskflow
    uvicorn app.main:app --reload
"""

import os
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/taskflow"
)
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="TaskFlow")


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskPatch(BaseModel):
    done: bool


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.on_event("startup")
def create_schema():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/tasks")
def list_tasks():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, title, done, created_at FROM tasks ORDER BY done, id DESC"
        ).fetchall()


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskIn):
    with get_conn() as conn:
        return conn.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done, created_at",
            (task.title.strip(),),
        ).fetchone()


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, patch: TaskPatch):
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE tasks SET done = %s WHERE id = %s RETURNING id, title, done, created_at",
            (patch.done, task_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
