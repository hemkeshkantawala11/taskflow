"""Operational endpoints that Kubernetes, Prometheus and the release process rely on."""

from app import main


def test_liveness(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_readiness_reports_database(client):
    res = client.get("/readyz")
    assert res.status_code == 200
    assert res.json()["database"] == "ok"


def test_readiness_fails_when_database_unreachable(client, monkeypatch):
    monkeypatch.setattr(main.db, "ping", lambda: False)
    res = client.get("/readyz")
    assert res.status_code == 503


def test_version_exposes_build_metadata(client):
    body = client.get("/version").json()
    assert set(body) == {"version", "git_sha", "build_time", "pod"}


def test_metrics_use_route_templates_not_raw_paths(client):
    client.post("/api/tasks", json={"title": "metric me"})
    client.delete("/api/tasks/12345")  # 404 on a templated route
    text = client.get("/metrics").text
    assert 'route="/api/tasks/{task_id}"' in text
    assert "/api/tasks/12345" not in text
    assert "taskflow_tasks_created_total" in text
    assert "taskflow_build_info" in text


def test_probe_endpoints_are_not_counted_in_request_metrics(client):
    client.get("/healthz")
    text = client.get("/metrics").text
    assert 'route="/healthz"' not in text


def test_chaos_injection_returns_500(client, monkeypatch):
    monkeypatch.setattr(main, "settings", main.settings.__class__(chaos_error_rate=1.0))
    assert client.get("/api/tasks").status_code == 500
    assert client.get("/healthz").status_code == 200  # never affects probes
    # Counted under the real route, so the /api SLO rules see injected failures.
    text = client.get("/metrics").text
    assert 'http_requests_total{method="GET",route="/api/tasks",status="500"}' in text
    assert 'route="unmatched"' not in text
