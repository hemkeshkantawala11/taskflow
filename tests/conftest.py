"""Tests run against a real PostgreSQL (a service container in CI).

Connection settings come from the same DB_* environment variables the app uses.
"""

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import db
from app.config import settings
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # runs the lifespan: opens pool, creates schema
        yield c


@pytest.fixture(autouse=True)
def clean_tasks(client):
    with psycopg.connect(settings.conninfo) as conn:
        conn.execute("TRUNCATE tasks RESTART IDENTITY")
    yield


@pytest.fixture
def pool():
    return db.pool
