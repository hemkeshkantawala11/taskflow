# Configuration drift and Argo CD selfHeal (2026-10-17)

Two hand edits to the live cluster, with Argo CD's automated sync and `selfHeal: true`.

## A. Adding an env var to the Deployment: not detected

The original demo (`kubectl set env deploy/taskflow LOG_LEVEL=DEBUG`):

```
07:11:35 before: env = DB_USER DB_PASSWORD POD_NAME
deployment.apps/taskflow env updated
07:11:35 after manual edit: env = DB_USER DB_PASSWORD POD_NAME LOG_LEVEL
07:11:36 argo=Synced/Healthy
07:11:38 argo=Synced/Progressing      <- the Deployment rolls new pods with the extra var
07:12:15 argo=Synced/Healthy
07:13:50 env: DB_USER DB_PASSWORD POD_NAME LOG_LEVEL   sync=Synced
```

Argo CD stayed `Synced` and never removed the variable: it diffs only the fields it applied,
and this list entry was never part of the chart. The variable was removed by hand
(`kubectl set env deploy/taskflow LOG_LEVEL-`), and the demo was changed to test a managed
field instead (commit `654c9d0`).

## B. Changing a value Argo CD manages: reverted within a second

```
$ kubectl -n taskflow patch configmap taskflow --type merge -p '{"data":{"LOG_LEVEL":"DEBUG"}}'
07:14:31 patching ConfigMap LOG_LEVEL=DEBUG
07:14:31 argo=Synced/Progressing LOG_LEVEL=DEBUG
07:14:32 argo=Synced/Healthy LOG_LEVEL=INFO       <- selfHeal re-applied Git's value
```

**Conclusion:** selfHeal enforces everything the chart declares. Closing the "additions" gap
would need RBAC without write access for people, or an admission policy (see
[decisions.md](../decisions.md)).
