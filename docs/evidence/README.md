# Evidence

Everything here was collected on the local kind cluster between 2026-10-13 and 2026-10-17.
**Evidence version: release 6, source commit `a0f7b71`, release commit `7cce9cb`**, image
`ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5`.
Problems found along the way are written up in [../incidents.md](../incidents.md).

## One version, end to end

| # | Checklist item | Evidence |
|---|---|---|
| 1 | Baseline vs final | PR "Files changed"; baseline `8b2761a` on `main` |
| 2 | Green pipeline for the source commit | [run 39014215134](https://github.com/hemkeshkantawala11/taskflow/actions/runs/39014215134), all jobs in [02-releases.md](02-releases.md) |
| 3 | Release approved by a person | GitHub approvals API, every release: [02-releases.md](02-releases.md) |
| 4 | Release commit naming image, source commit and run | `7cce9cb`, quoted in [02-releases.md](02-releases.md) |
| 5 | Argo CD synced, Healthy, running that image | [01-verify-release-a0f7b71.md](01-verify-release-a0f7b71.md) §2, screenshot `argocd-app.png`. Synced revision is `9f28e3a`: the demo commits after `7cce9cb` changed config only and the last one (the rollback) restored the same image tag |
| 6 | Pods running image `:a0f7b71…` | [01-verify-release-a0f7b71.md](01-verify-release-a0f7b71.md) §3 |
| 7 | Users served by that version | [01-verify-release-a0f7b71.md](01-verify-release-a0f7b71.md) §4 |
| 8 | User journey works | [01-verify-release-a0f7b71.md](01-verify-release-a0f7b71.md) §5 (smoke test) |
| 9 | Dashboard with traffic | screenshots `grafana-errors.png`, `grafana-recovered.png` |
| 10 | Log line → trace with SQL span | [03-log-to-trace.md](03-log-to-trace.md); screenshot `loki-logs.png` (JSON logs with `trace_id`, error lines during the demo) |
| 11 | Alert firing and resolving | [08-errors-alert.md](08-errors-alert.md), screenshot `alertmanager-firing.png` |
| 12 | Rollback | [09-bad-release-rollback.md](09-bad-release-rollback.md) |
| 13 | Security gates | Security job of the run above (gitleaks, pip-audit, Trivy config) and Trivy image scan in the build job |

## Behaviour under change and failure

| File | What it shows |
|---|---|
| [02-releases.md](02-releases.md) | 6 releases; every rollout recorded under live traffic with zero failed requests |
| [04-autoscaling.md](04-autoscaling.md) | HPA 2 → 5 under load (release `ea5c829`, before the list-endpoint fix) |
| [05-cluster-restart.md](05-cluster-restart.md) | Whole cluster stopped for 3 days and restarted: state and data intact |
| [06-db-kill.md](06-db-kill.md) | PostgreSQL pod deleted: recreated, data kept, web pods not restarted |
| [07-drift.md](07-drift.md) | Hand edits: managed field reverted by selfHeal in ~1 s; an added field is not drift |
| [08-errors-alert.md](08-errors-alert.md) | Fault injected via Git → SLO alert fires → reverted → resolves |
| [09-bad-release-rollback.md](09-bad-release-rollback.md) | Broken image tag → old pods keep serving → `git revert` |

## Screenshots ([screenshots/](screenshots/), browser chrome cropped)

| File | Shows |
|---|---|
| `grafana-errors.png` | Dashboard during the errors demo: availability 92.9%, burn rate 7.1, error ratio rising, build `a0f7b71` |
| `alertmanager-firing.png` | `TaskflowHighErrorRate` (critical) active in Alertmanager since 07:46:28 |
| `grafana-recovered.png` | The same dashboard over 30 minutes: error spike and recovery |
| `loki-logs.png` | Grafana Explore on Loki: JSON request logs with `trace_id`; error-level lines during the demo |
| `argocd-app.png` | Argo CD application `taskflow` Synced / Healthy |
