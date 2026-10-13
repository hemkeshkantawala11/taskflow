# Failure demonstrations

Each demo follows: **symptom → hypothesis → evidence → change → verification.**
Keep `make ui` and `make load` running, with the Grafana dashboard open.

## 1. Bad release, safe rollback (release control)

```bash
make demo-bad-release
```
- **Symptom:** the Argo CD app is Degraded/Progressing; one new pod shows `ImagePullBackOff`.
- **Hypothesis:** the release points at an image that doesn't exist.
- **Evidence:** `kubectl -n taskflow describe pod <new-pod>` shows the pull error. The "Running build"
  panel still shows only the old SHA. `make smoke` still passes, because old pods kept serving
  (`maxUnavailable: 0`).
- **Change:** `git revert --no-edit HEAD && git push` (the Git history records the rollback).
- **Verify:** the new pod disappears, Argo CD returns to Synced/Healthy, and `make smoke` passes.

## 2. Error budget burn (observability → alert → response)

```bash
make demo-errors-on      # commits chaosErrorRate: "0.3" (Argo CD applies it)
```
- **Symptom:** the error ratio panel jumps to ~30%, availability goes red, and after ~2 min
  `TaskflowHighErrorRate` fires (Prometheus → Alerts, or Alertmanager).
- **Hypothesis:** a config change, not a code change, is causing it (the build SHA is unchanged).
- **Evidence:** the "Error logs" panel shows 500s on all `/api` routes; `git log` shows the config commit.
- **Change:** `make demo-errors-off`.
- **Verify:** the ratio returns to 0, the alert resolves, and `make smoke` passes.

## 3. Database pod dies (state and dependency failure)

```bash
make demo-db
```
- **Symptom:** API errors for a few seconds; web pods go NotReady.
- **Evidence:** the "Database reachable" panel shows DOWN; web pods are **not** restarted (check the
  RESTARTS column); `taskflow-postgres-0` is recreated with the same name.
- **Verify:** pods are Ready again, and the task created before the kill still exists, because the
  data lives on the PVC.

## 4. Configuration drift (GitOps self-healing)

```bash
make demo-drift
```
- **Symptom:** someone edits the Deployment by hand (`LOG_LEVEL=DEBUG`).
- **Evidence:** Argo CD briefly shows OutOfSync, then selfHeal re-applies Git's version and the
  extra env var disappears.
- **Point to make:** Git is the source of truth; manual changes don't survive, so what's running
  always matches what was reviewed.

## Questions to rehearse ("what would change?")

- *Node fails:* topology spread put web pods on both workers, so one survives and the PDB protects
  drains. Postgres is single-instance, so it's unavailable until rescheduled (and with kind
  local-path storage, its data is tied to that node).
- *10× traffic:* the HPA scales to 5 pods. Next bottlenecks are DB connections (5 pods × pool 5 = 25)
  and CPU on the DB, so add a pooler (PgBouncer) or read replicas.
- *Real users:* canary releases with Argo Rollouts plus automated analysis on the error-ratio
  query, TLS via cert-manager, a managed database with backups, and an Alertmanager receiver
  (Slack or PagerDuty).
