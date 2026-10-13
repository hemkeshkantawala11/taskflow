# Architecture

## Components

| Component | Kind | Why it exists | If it fails |
|---|---|---|---|
| `taskflow` web (2–5 pods) | Deployment + HPA | Serves UI and API. Stateless, so any pod can answer any request. | Other replicas keep serving. Readiness removes a bad pod from the Service. |
| `taskflow-postgres-0` | StatefulSet + PVC | Stores tasks. Stable name and its own volume. | API returns errors; app pods go NotReady (readiness checks the DB) but are **not restarted** (liveness doesn't). Data survives a pod restart. |
| Traefik | Deployment (NodePort 30080) | The only entry point from outside. Routes `taskflow.localtest.me` to the Service. | Site unreachable from outside; inside the cluster everything still works. |
| Prometheus, Alertmanager, Grafana, kube-state-metrics | kube-prometheus-stack | Metrics, SLO rules, alerts, dashboards. | No visibility. The app itself is unaffected. |
| Loki + Alloy | Helm charts | Central, searchable logs. | Logs still available with `kubectl logs`. |
| Jaeger | Deployment | Receives traces over OTLP/HTTP. | Spans are dropped by the exporter; the app is unaffected (export is async and batched). |
| Argo CD | Helm chart | Makes the cluster match Git. | No new releases, no drift correction. Running workloads are unaffected. |
| GitHub Actions + GHCR | SaaS | Tests, scans, builds, publishes, records the release in Git. | No new releases. |

## Request path

1. Browser → `http://taskflow.localtest.me:8080`. `localtest.me` resolves to 127.0.0.1.
2. Docker forwards host port 8080 to node port 30080 on the kind control-plane node
   (`deploy/kind/cluster.yaml`).
3. kube-proxy forwards NodePort 30080 to the Traefik pod.
4. Traefik matches the Ingress host rule and picks a **ready** endpoint of Service `taskflow`.
   NetworkPolicy `taskflow-web` allows this because it comes from the `traefik` namespace.
5. The FastAPI pod handles it. The OpenTelemetry middleware starts a span, the metrics
   middleware times it, and a JSON log line with the `trace_id` is written to stdout.
6. A connection is borrowed from the pool and SQL is sent to `taskflow-postgres:5432`
   (headless Service → pod DNS). Only web pods may connect (NetworkPolicy).
7. The response goes back the same way. The pod then exports the trace to Jaeger
   (allowed: egress to `observability` namespace, port 4318).

## Change path (commit → running)

1. `git push` to `devops/platform` (or `main`).
2. GitHub Actions runs in parallel: **test** (ruff, pytest against Postgres), **security**
   (gitleaks over full history, pip-audit, Trivy misconfiguration scan), **config** (helm lint,
   kubeconform schema validation, promtool unit tests of the alert rules).
3. **build**: Docker image with `GIT_SHA` baked in → Trivy image scan → container smoke test
   (checks `/version` returns that SHA) → push `ghcr.io/<owner>/taskflow:<full-sha>` as a
   multi-arch image (`linux/amd64` + `linux/arm64`, so it also runs on Apple Silicon kind nodes).
4. **deploy**: waits for approval on the `local` environment, then commits the new tag to
   `values-local.yaml` with a message naming the image, source commit and pipeline run.
5. Argo CD polls Git (60 s), renders the chart, sees the Deployment's image changed and applies it.
6. Kubernetes rolling update: one extra pod starts (`maxSurge: 1`); only after it passes
   readiness for 5 s (`minReadySeconds`) is an old pod removed (`maxUnavailable: 0`).
   The old pod gets `preStop: sleep 5` so Traefik stops sending to it before shutdown.

## Trust boundaries and exposure

- Exposed outside the cluster: only Traefik, bound to `127.0.0.1:8080` on the host.
- `/metrics` is not routed by the Ingress; only Prometheus (monitoring namespace) can reach it.
- Tool UIs (Grafana, Argo CD, …) are reachable only through `kubectl port-forward`,
  which requires cluster credentials.
- Namespace `taskflow` enforces the **restricted** Pod Security Standard and default-deny
  NetworkPolicies.
- CI holds no cluster credentials at all: the cluster pulls from Git (Argo CD) and GHCR.
