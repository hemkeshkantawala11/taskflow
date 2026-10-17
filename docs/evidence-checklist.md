# Evidence checklist (rubric: verification and operational evidence, 10 marks)

Collect these for **one specific version** so they connect. Save screenshots in `docs/evidence/`
and link this file from the PR.

| # | Evidence | How |
|---|---|---|
| 1 | Baseline commit vs final commit | The PR's "Files changed" tab |
| 2 | Green pipeline run for source commit `X` | Actions run page: all jobs, the image tag in the summary |
| 3 | Approval of the release | Deploy job showing who approved |
| 4 | Release commit naming image `X` and the run URL | `git show <deploy commit>` |
| 5 | Argo CD synced to that commit, Healthy | Argo CD UI or `make verify` section 2 |
| 6 | Pods running image `…:X` | `make verify` section 3 |
| 7 | Users served by `X` | `make verify` section 4 + the build strip in the UI |
| 8 | User journey works | `make verify` section 5 (smoke test) |
| 9 | Dashboard with traffic | Grafana "TaskFlow overview" screenshot |
| 10 | A trace with SQL spans, reached from a log line | Loki log → TraceID → Jaeger screenshot |
| 11 | An alert firing and resolving | Demo 2 in fault-demo.md: Alertmanager or Prometheus screenshots |
| 12 | A rollback | Demo 1: revert commit + Argo CD history |
| 13 | Security gates | Security job log (gitleaks, pip-audit, Trivy) |
| 14 | Recorded walkthrough (optional, recommended) | 5–8 min screen recording following this table |
