# Design decisions and tradeoffs

Each entry: what was chosen, why, the credible alternative, and when the alternative would be better.

## Application

**FastAPI + PostgreSQL, one small service.** The guide asks for a manageable app; one
service plus a real database exercises stateful storage, dependencies and failure
boundaries without microservice overhead. *Switch to more services* only if parts
scale or release independently.

**Liveness ≠ readiness.** `/healthz` only says "the process responds"; `/readyz` also
checks the database. If Postgres is down, restarting web pods fixes nothing and causes
churn, so liveness must not depend on it. Readiness removes pods from the load balancer
instead. A **startupProbe** gives slow starts up to 60 s without making liveness lenient.

**Connection pool, background open, advisory-locked schema creation.** Pods start even
before the DB is ready (no crash loops, no init-container ordering), and concurrent
replicas can't race on `CREATE TABLE`. *Alternative:* a dedicated migration Job (Helm
hook / Argo sync hook) with a tool like Alembic. Better once the schema changes often or
migrations are destructive.

**One uvicorn worker per pod.** Scaling happens by adding pods (HPA), which keeps
Prometheus metrics per-process simple. *Alternative:* multiple workers per pod with
Prometheus multiprocess mode, useful when pod count is constrained.

## Kubernetes

**Deployment for the web tier, StatefulSet for Postgres.** The web tier is stateless and
interchangeable. Postgres needs a stable identity and a volume that follows it.
*Alternative:* a managed database (RDS/Cloud SQL) or an operator (CloudNativePG) for
replication, backups and failover. Clearly better in production; out of scope locally.

**Resources: requests set, memory limit set, no CPU limit.** Requests drive scheduling and
the HPA's percentage. A memory limit contains leaks. CPU limits cause throttling and
latency spikes without protecting anything memory limits don't. *Use CPU limits* in
multi-tenant clusters with strict fairness requirements.

**HPA on CPU (2–5 replicas) + PDB minAvailable 1 + topology spread.** Two replicas
minimum, spread across nodes, so a node drain or failure leaves one serving.
*Alternative:* scale on request rate or latency via Prometheus Adapter/KEDA, better
when the bottleneck isn't CPU (e.g. waiting on the DB).

**Traefik with a standard Ingress.** ingress-nginx was retired in 2026; Traefik supports
the portable `networking.k8s.io/v1` Ingress, so the chart isn't tied to one controller.
*Alternative:* Gateway API (e.g. Envoy Gateway), the newer standard, with richer traffic
splitting (useful for canaries).

## Configuration

**One Helm chart, `values.yaml` + `values-<env>.yaml`.** Defaults live once; an
environment file holds only differences (today just the image tag). Adding staging means
adding `values-staging.yaml` and a second Argo CD Application, not copying manifests.
*Alternative:* Kustomize overlays. Simpler for patching plain YAML, weaker for
parameterisation and conditionals.

**ConfigMap checksum annotation.** A config change alters the pod template hash and
triggers a rolling restart; otherwise pods would keep stale environment variables.

## Delivery and release

**GitHub Actions for CI; Argo CD (pull-based GitOps) for CD.** GitHub's runners can't
reach a laptop cluster. Pull-based delivery also means CI holds **no cluster
credentials**. Git is the record of what should run, Argo CD's selfHeal corrects drift,
and rollback is `git revert`. *Alternatives:* a self-hosted runner doing `helm upgrade`
(push-based: simpler, but CI needs cluster admin, and self-hosted runners on public repos
are risky), or Argo CD Image Updater (avoids bot commits, adds a component).

**Release bot commits the image tag to the same branch.** Keeps every change in the one
PR the course requires. Tradeoff: you must `git pull` before pushing, and the final
commit can be a deploy commit. Each deploy commit names the source commit and pipeline
run, so traceability is preserved.

**Manual approval only before release.** Checks are fully automatic (fast feedback). A
human decides when users get the change, via a GitHub Environment with a required
reviewer. *Remove the gate* when test coverage and canary analysis are trusted enough
for continuous deployment.

**Rolling update with `maxUnavailable: 0`.** Zero downtime, and a release that never
becomes ready (bad image, failing readiness) stops after one new pod while the old pods
keep serving. *Blue-green* gives instant switch-back and full pre-production testing at
2× resources. *Canary* (Argo Rollouts) limits blast radius by percentage with automated
metric analysis, the next step if the user base were real.

**selfHeal covers managed fields, not additions.** Argo CD compares the fields it applied,
so a hand edit to anything in the chart (an image, a ConfigMap value) is reverted within
seconds, but a field it never set (an extra env var added with `kubectl set env`) is not
reported as drift. Verified on the cluster. *Mitigation if it mattered:* no write access for
humans in the namespace (RBAC) or an admission policy (Kyverno) that rejects manual edits.

**Immutable image tag = full git SHA.** The running version is unambiguous: pod image →
commit → pipeline run. `/version`, the `taskflow_build_info` metric, OCI labels and the
`app.kubernetes.io/version` pod label all expose it. `latest` is never used.

**Multi-arch image (amd64 + arm64).** CI runs on amd64, but kind on an Apple Silicon laptop
runs arm64 nodes, which cannot pull an amd64-only image ("no match for platform in
manifest"). The amd64 image is scanned and smoke-tested, then the same Dockerfile, build
args and layer cache produce an amd64 + arm64 manifest under the same SHA tag. Tradeoff:
the arm64 variant is built under QEMU emulation (slower) and is not separately scanned or
smoke-tested; it has the same pinned dependencies, and the cluster smoke test exercises it.
*Alternative:* native `ubuntu-24.04-arm` runners per architecture plus a manifest-merge job
(faster, more workflow plumbing).

## Observability

**RED metrics labelled by route template.** Rate, errors, duration per
`/api/tasks/{task_id}`, never per raw URL, which would create unbounded series.

**SLO: 99% of `/api` requests succeed; p95 < 500 ms.** Health/metrics endpoints are
excluded so probe traffic doesn't hide user-facing failures. Alerts use **multi-window
burn rates** (Google SRE workbook): page when the budget would be gone in ~2 days, warn
for slow drains. A short-window `TaskflowHighErrorRate` gives fast feedback during rollouts.
Each alert links to a runbook entry with concrete response steps.

**JSON logs with trace IDs; OpenTelemetry tracing.** Logs answer "what happened", traces
answer "where the time went" (including each SQL query). Grafana links a log line's
`trace_id` to its trace.

## Security

| Area | Control |
|---|---|
| Supply chain | Actions pinned to commit SHAs; tools checksum-verified; versions ≥ 2 weeks old; pinned dependencies |
| Secret scanning | gitleaks over full Git history on every run |
| Dependencies / image | pip-audit; Trivy image scan fails on fixable HIGH/CRITICAL |
| IaC | Trivy misconfiguration scan of Dockerfile + chart |
| CI permissions | `permissions: {}` by default; per-job least privilege; short-lived `GITHUB_TOKEN` |
| Deploy permissions | Argo CD AppProject: only this repo → only `taskflow` namespace, no cluster-scoped resources |
| Runtime | Non-root UID, read-only root filesystem, all capabilities dropped, seccomp, restricted PSS enforced |
| Identity | Dedicated ServiceAccount, no RBAC, no API token mounted |
| Network | Default-deny NetworkPolicies; explicit allow list |
| Secrets | Generated in-cluster by script; never in Git or images |
| Exposure | Only Traefik exposed, on 127.0.0.1; `/metrics` and tool UIs not exposed |

**Secrets created by script rather than Sealed Secrets / External Secrets.** Nothing
secret, even encrypted, enters Git, and there are fewer moving parts. Tradeoff: secrets
aren't declarative, so a rebuilt cluster needs the script re-run. *Use Sealed Secrets or
External Secrets Operator + a vault* when several people or clusters need the same secrets.

**Accepted low/medium scanner findings:** no CPU limits (see above); Postgres runs as
UID 70 (the image's postgres user); Dockerfile has no HEALTHCHECK (Kubernetes probes
replace it); "trusted registries" (enforce with an admission policy such as Kyverno in a
real cluster); ConfigMap "sensitive content" is a false positive (key names `DB_PORT`, `LOG_LEVEL`).
