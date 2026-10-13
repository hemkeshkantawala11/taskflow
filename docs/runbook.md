# Runbook

Every TaskFlow alert links here. Start with: `make status`, the Grafana dashboard
"TaskFlow overview", and `kubectl -n taskflow get events --sort-by=.lastTimestamp | tail`.

## TaskflowErrorBudgetFastBurn

**Meaning:** over both the last hour and last 5 minutes, more than 14.4% of `/api`
requests failed. At this rate the 30-day budget (1%) is gone in about 2 days.
**Response:**
1. Did a release just happen? Compare the "Running build" panel with `git log`. If yes, `make rollback`.
2. Otherwise check `TaskflowDatabaseUnreachable` and pod status.
3. Grafana → Explore → Loki: `{namespace="taskflow"} | json | level="error"`; open a `trace_id` in Jaeger.
**Verify recovery:** the 5m error ratio drops below 1%; the alert resolves; `make smoke` passes.

## TaskflowErrorBudgetSlowBurn

**Meaning:** a sustained error rate around 6% (6× budget) over 6 hours.
**Response:** not urgent, but find the failing route ("Responses by status" panel), read
its error logs and fix forward. Check whether `chaosErrorRate` was left on in `values-local.yaml`.

## TaskflowHighErrorRate

**Meaning:** more than 5% of API requests failed over 5 minutes (fast symptom alert).
**Response:** same as FastBurn. During a rollout, watch `kubectl -n taskflow rollout status deploy/taskflow`.

## TaskflowHighLatency

**Meaning:** p95 latency above 500 ms for 5 minutes.
**Response:**
1. CPU per pod near the request? Check the HPA (`kubectl -n taskflow get hpa`); is it at max replicas?
2. Slow SQL? Open a slow trace in Jaeger and see which span dominates.
3. Pool exhaustion: many requests waiting means raising `app.dbPoolMax` (within Postgres `max_connections`).

## TaskflowDatabaseUnreachable

**Meaning:** no web pod's readiness check can reach PostgreSQL.
**Response:**
1. `kubectl -n taskflow get pod taskflow-postgres-0` and `kubectl -n taskflow logs taskflow-postgres-0`.
2. Pending? Check the PVC (`kubectl -n taskflow get pvc`). CrashLoop? Read the logs (disk full, bad credentials).
3. Was a NetworkPolicy changed? `kubectl -n taskflow get networkpolicy`.
**Expected behaviour:** web pods turn NotReady (no traffic) but are not restarted.
**Verify:** `taskflow_db_up` returns to 1; pods Ready; smoke test passes; existing tasks still present.

## TaskflowNoReadyPods

**Meaning:** zero available web pods, so users get errors from the ingress.
**Response:** `kubectl -n taskflow describe pods -l app.kubernetes.io/component=web`.
ImagePullBackOff → bad tag: `make rollback`. CrashLoopBackOff → `kubectl logs --previous`.
NotReady → the database (see above).

## TaskflowRolloutStuck

**Meaning:** a new version hasn't finished rolling out after 5 minutes.
**Response:** `kubectl -n taskflow rollout status deploy/taskflow` and describe the new pod.
Old pods are still serving (`maxUnavailable: 0`), so there is no user impact yet. Roll back
with `make rollback` rather than `kubectl rollout undo`, because Argo CD would immediately
re-apply what Git says.
