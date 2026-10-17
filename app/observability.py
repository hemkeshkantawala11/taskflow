"""Logs, metrics and traces for TaskFlow.

- Logs: one JSON object per line on stdout. Kubernetes collects stdout; Loki
  (via Grafana Alloy) stores it. Every line carries trace_id so a log line can
  be joined to its trace in Jaeger.
- Metrics: RED metrics (Rate, Errors, Duration) per route, exposed on /metrics
  for Prometheus. Routes are labelled by template (/api/tasks/{task_id}), never
  by raw path, to keep label cardinality bounded.
- Traces: OpenTelemetry spans for each request and each SQL query, exported
  over OTLP/HTTP to Jaeger. Enabled with OTEL_ENABLED=true.
"""

import json
import logging
import sys
import time
from datetime import UTC, datetime

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import settings

try:  # tracing is optional at runtime but installed in the image
    from opentelemetry import trace
except ImportError:  # pragma: no cover
    trace = None


# ---------------------------------------------------------------- logging
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
            "pod": settings.pod_name,
            "version": settings.app_version,
        }
        if trace is not None:
            ctx = trace.get_current_span().get_span_context()
            if ctx.is_valid:
                entry["trace_id"] = format(ctx.trace_id, "032x")
                entry["span_id"] = format(ctx.span_id, "016x")
        for key in ("method", "route", "path", "status", "duration_ms"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
    # We log requests ourselves (with route + trace id), so silence uvicorn's access log.
    logging.getLogger("uvicorn.access").disabled = True


# ---------------------------------------------------------------- metrics
LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

HTTP_REQUESTS = Counter(
    "http_requests_total", "HTTP requests handled", ["method", "route", "status"]
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "route"],
    buckets=LATENCY_BUCKETS,
)
TASKS_CREATED = Counter("taskflow_tasks_created_total", "Tasks created")
DB_UP = Gauge("taskflow_db_up", "1 if the last readiness check reached the database")
BUILD_INFO = Gauge(
    "taskflow_build_info", "Build metadata of the running process", ["version", "git_sha"]
)
BUILD_INFO.labels(version=settings.app_version, git_sha=settings.git_sha).set(1)

# Probe and scrape endpoints are excluded so they don't dilute the user-facing SLO.
UNMEASURED_PATHS = {"/metrics", "/healthz", "/readyz"}

access_log = logging.getLogger("taskflow.access")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNMEASURED_PATHS:
            return await call_next(request)
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            route = _route_template(request)
            HTTP_REQUESTS.labels(request.method, route, str(status)).inc()
            HTTP_LATENCY.labels(request.method, route).observe(elapsed)
            level = logging.ERROR if status >= 500 else logging.INFO
            access_log.log(
                level,
                "request",
                extra={
                    "method": request.method,
                    "route": route,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": round(elapsed * 1000, 2),
                },
            )


# ---------------------------------------------------------------- tracing
def setup_tracing(app) -> None:
    if not settings.otel_enabled:
        return
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": "taskflow",
            "service.version": settings.app_version,
            "service.instance.id": settings.pod_name,
            "vcs.revision": settings.git_sha,
        }
    )
    provider = TracerProvider(resource=resource)
    # Endpoint comes from OTEL_EXPORTER_OTLP_ENDPOINT (standard OTel variable).
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    PsycopgInstrumentor().instrument(enable_commenter=False)
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="healthz,readyz,metrics",
        exclude_spans=["send", "receive"],  # keep traces readable
    )
    logging.getLogger("taskflow").info("tracing enabled")
