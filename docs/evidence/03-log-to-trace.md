# Log line → trace (release a0f7b71)

Collected 2026-10-17 07:59 UTC while `make load` was running. The log line's `span_id` is the trace's
root span, and the `INSERT` span is its child: one request followed from Loki to Jaeger, including SQL.

## Log line in Loki
LogQL: `{namespace="taskflow", container="taskflow"} |= "\"method\": \"POST\"" |= "trace_id"`

Labels: `{"namespace": "taskflow", "pod": "taskflow-c6545448-t9jhn", "container": "taskflow"}`

```json
{
 "ts": "2026-10-17T07:58:33.320817+00:00",
 "level": "info",
 "logger": "taskflow.access",
 "msg": "request",
 "pod": "taskflow-c6545448-t9jhn",
 "version": "1.0.13",
 "trace_id": "30a95fd9c2e1e0988a548d09c9263b30",
 "span_id": "71a64f382aba9443",
 "method": "POST",
 "route": "/api/tasks",
 "path": "/api/tasks",
 "status": 201,
 "duration_ms": 2.13
}
```

## Same trace in Jaeger (`/api/v3/traces/30a95fd9c2e1e0988a548d09c9263b30`)

| span | parent | duration | key attributes |
|---|---|---|---|
| `INSERT` | 71a64f38 | 0.59 ms | `{"db.statement": "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done, created_at", "db.system": "postgresql", "net.peer.name": "taskflow-postgres"}` |
| `POST /api/tasks` | root | 2.59 ms | `{"http.route": "/api/tasks", "http.status_code": "201"}` |

Resource: service `taskflow`, pod `taskflow-c6545448-t9jhn`, version `1.0.13`, git `a0f7b71eea781c3ebc1d42b08e8a63d43281afd5`
