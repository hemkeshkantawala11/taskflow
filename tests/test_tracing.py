"""Tracing: user requests produce SQL spans, readiness probes do not."""

import pytest
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app import db


@pytest.fixture
def spans(client, monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    PsycopgInstrumentor().instrument(tracer_provider=provider, skip_dep_check=True)
    # Only connections opened after instrumenting are traced (as in the app, where
    # tracing is set up before the pool opens), so use a fresh pool for these tests.
    monkeypatch.setattr(db, "pool", db.pool)  # restored after the test
    fresh = db.open_pool()
    fresh.wait()
    try:
        yield exporter
    finally:
        fresh.close()
        PsycopgInstrumentor().uninstrument()


def test_readiness_ping_is_not_traced(client, spans):
    assert db.ping()
    assert spans.get_finished_spans() == ()


def test_queries_are_traced(client, spans):
    with db.pool.connection() as conn:
        conn.execute("SELECT 1")
    assert [s.name for s in spans.get_finished_spans()] == ["SELECT"]
