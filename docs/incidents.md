# Incidents and first-run fixes

Problems found while running the platform for real, in the order they happened. Each one
follows the same method: symptom → hypothesis → evidence → smallest change → verification.

## 1. Image would not run on the local cluster (CPU architecture)

- **Symptom (predicted before the first release):** CI builds on `ubuntu-24.04` (amd64), but
  the laptop is an Apple Silicon Mac, so kind's nodes are `linux/arm64`. An amd64-only image
  fails to pull with `no match for platform in manifest`.
- **Evidence:** `uname -m` → `arm64`; `docker version` → server `linux/arm64`; the workflow
  built with no `platforms` setting.
- **Change:** the build job still scans and smoke-tests the amd64 image, then pushes a
  multi-arch manifest (`linux/amd64` + `linux/arm64`) under the same SHA tag, using QEMU.
  Tradeoff recorded in [decisions.md](decisions.md).
- **Verify:** `docker buildx imagetools inspect ghcr.io/hemkeshkantawala11/taskflow:<sha>`
  lists both platforms; pods start on the arm64 nodes.

## 2. `make cluster` failed once: `lookup github.com: no such host`

- **Symptom:** Helm could not download the metrics-server chart.
- **Evidence:** a minute later `dscacheutil -q host -a name github.com` resolved and
  `helm pull` of the same chart succeeded, so it was a transient DNS failure on the laptop.
- **Change:** none; re-ran `make cluster`, which is idempotent.

## 3. Readiness probes flooded Jaeger with one-span traces

- **Symptom:** in Jaeger, 38 traces containing only a `SELECT` against 1 real request trace.
- **Hypothesis:** `/readyz` is excluded from request tracing, but its `SELECT 1` was still
  traced, so every probe (every 5 s per pod) became its own root trace.
- **Evidence:** the `SELECT` root spans arrived every ~5 s per pod; real requests showed
  `GET /api/tasks` → `SELECT` correctly.
- **Change:** `db.ping()` runs under `suppress_instrumentation()` (commit `c03d002`), with
  tests that probes produce no spans while API queries still do. Removing the fix makes the
  test fail (negative control).
- **Verify:** after release 2 the new pods sent no probe traces; only requests and one
  schema-lock span per pod at startup.

## 4. Argo CD stayed "Progressing" after every successful sync

- **Symptom:** app `Synced`, all pods Ready, but health never reached `Healthy`.
- **Hypothesis:** Argo CD's Ingress health check waits for `status.loadBalancer.ingress`.
- **Evidence:** the Ingress status was `{}`. Traefik copies it from its own Service
  (`publishedService`), which is a NodePort and has no load-balancer address.
- **Change:** Traefik publishes `127.0.0.1` (`ingressEndpoint.ip`), the address kind maps to
  the host (commit `18c9d71`).
- **Verify:** Ingress ADDRESS `127.0.0.1`; Argo CD `Synced/Healthy`.

## 5. `make verify` "Signals" section crashed

- **Symptom:** `exec: "wget": executable file not found` and a Python `SyntaxError`.
- **Cause:** the current Prometheus image no longer ships `wget`; the alert summary used
  backslash-escaped quotes inside an f-string expression.
- **Change:** query Prometheus through the API server's service proxy
  (`kubectl get --raw .../services/...:9090/proxy/...`), which needs no tools in the
  container (commit `a66ca77`).

## 6. Fault demos would fail on macOS

- **Symptom:** `sed: \1 not defined in the RE`; the bad-release demo committed nothing.
- **Cause:** GNU `sed -i -E` is parsed differently by BSD sed (macOS).
- **Change:** use `perl -pi -e`, identical on both; demo and rollback targets also rebase
  before pushing, because CI adds release commits to the branch (commit `ea5c829`).

## 7. Dashboard "Running build" listed builds that were no longer running

- **Symptom:** three builds shown, one running.
- **Cause:** a range query reduced with `lastNotNull` keeps every series seen in the window.
- **Change:** instant query (commit `28bb5ba`). Mid-rollout it still shows both versions.

## 8. Brief `Degraded` in Argo CD right after each rollout (accepted)

- **Symptom:** ~15 s of `Degraded` after a rollout completes, then `Healthy`.
- **Evidence:** HPA event `did not receive metrics for targeted pods (pods might be
  unready)`: brand-new pods have no CPU sample until metrics-server's next scrape.
- **Decision:** accepted; it is self-clearing and does not affect traffic (all requests
  succeeded during every rollout).

## 9. Load generator stopped when the laptop slept

- **Symptom:** `make load` exited with curl code 28 (timeout) after the Mac slept.
- **Cause:** `demo.sh` uses `set -e`, so one failed request ends the loop.
- **Decision:** accepted for a demo tool; run it as `caffeinate -i make load` on macOS.

## 10. Whole cluster stopped from outside

- **Symptom:** API server unreachable; all three kind node containers exited (137).
- **Evidence:** `docker events` showed an ordinary `docker stop` of each node in turn
  (stop signal 37, then 9), not an OOM kill.
- **Recovery:** `docker start taskflow-control-plane taskflow-worker taskflow-worker2`.
  See [evidence/05-cluster-restart.md](evidence/05-cluster-restart.md) for what came back
  and how long it took.

## 11. kubectl pointed at a different cluster

- **Symptom:** after the restart, `kubectl get nodes` timed out against an unrelated remote
  cluster: the laptop's current kubectl context had been switched for other work.
- **Risk:** the `make` targets and demo scripts act on the *current* context, so
  `make demo-db` would have tried to delete a pod in the wrong cluster.
- **Change:** all operations from then on used an isolated kubeconfig
  (`kind get kubeconfig --name taskflow > …; export KUBECONFIG=…`); the README now warns about
  this. *Better fix if continued:* have the scripts refuse to run unless the context is
  `kind-taskflow`.

## 12. List endpoint grew without bound under load

- **Symptom:** after load testing, `make load` managed only ~1.3 req/s and the HPA sat at
  its maximum of 5 pods.
- **Evidence:** `GET /api/tasks` returned all 26,512 rows the load generator had created:
  2.3 MB and ~130 ms per response, spent serialising JSON.
- **Change:** `limit` query parameter, default 100, maximum 500 (commit `87f6a20`), with a
  test. See the release 5 evidence for the effect.

## 13. Drift demo claimed something Argo CD does not do

- **Symptom:** `make demo-drift` added an env var with `kubectl set env`; Argo CD stayed
  `Synced` and never removed it.
- **Cause:** Argo CD diffs the fields it applied; an extra list entry is not drift to it.
- **Change:** the demo now edits `LOG_LEVEL` in the managed ConfigMap, which selfHeal reverted
  within a second; the limit is documented (commit `654c9d0`,
  [evidence/07-drift.md](evidence/07-drift.md)).

## 14. Injected errors were invisible to the SLO (no alert fired)

- **Symptom:** errors demo on (`chaosErrorRate: 0.3`, commit `e461eab`); ~30% of `/api`
  requests returned 500, but `taskflow:api_error_ratio:rate5m` stayed at 0% for 12 minutes and
  no alert fired.
- **Hypothesis:** the failures were not being counted under an `/api` route.
- **Evidence:** `sum by (route,status)(increase(http_requests_total{status="500"}[15m]))`
  → 3,931 errors, all `route="unmatched"`. The injection was middleware that returned before
  routing, so the metrics middleware found no route template. The SLO rules select
  `route=~"/api/.*"`. The old test only checked the status code.
- **Why it matters beyond the demo:** any failure raised before routing would be invisible
  to the error budget.
- **Change:** injection is a route dependency (runs after routing); the test now asserts
  the 500 is counted under `route="/api/tasks"` and fails against the old code (commit
  `a0f7b71`). Errors switched off again in `3154fe7`.
- **Verify:** the errors demo on release 6 ([evidence/08-errors-alert.md](evidence/08-errors-alert.md)).
