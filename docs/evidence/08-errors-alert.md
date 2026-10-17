# Error-budget alert: fire and resolve (release a0f7b71)

Fault injected through Git (`make demo-errors-on` → commit `692fa31`, `chaosErrorRate: "0.3"`), applied
by Argo CD, removed the same way (`make demo-errors-off` → `88cf1e8`). `make load` ran throughout.
The first attempt on release 654c9d0 found the bug in incident 14 (no alert fired); this is the rerun
on the fixed release.

Alert rule: `TaskflowHighErrorRate` = 5m error ratio > 5% for 2m (critical). Timeline from the
Prometheus and Alertmanager APIs:

```
== 07:42:43 errors ON
scripts/demo.sh errors-on
[devops/platform 692fa31] demo: set chaosErrorRate="0.3" [skip ci]
07:42:49 5m error ratio=0.0% alerts=none
07:43:05 5m error ratio=0.0% alerts=TaskflowRolloutStuck=pending
07:43:20 5m error ratio=0.0% alerts=TaskflowRolloutStuck=pending
07:43:35 5m error ratio=0.5% alerts=none
07:43:50 5m error ratio=0.5% alerts=none
07:44:05 5m error ratio=4.3% alerts=none
07:44:20 5m error ratio=4.3% alerts=none
07:44:35 5m error ratio=7.6% alerts=TaskflowHighErrorRate=pending
07:44:50 5m error ratio=7.6% alerts=TaskflowHighErrorRate=pending
07:45:05 5m error ratio=10.6% alerts=TaskflowHighErrorRate=pending
07:45:21 5m error ratio=10.6% alerts=TaskflowHighErrorRate=pending
07:45:36 5m error ratio=13.3% alerts=TaskflowHighErrorRate=pending
07:45:51 5m error ratio=16.8% alerts=TaskflowHighErrorRate=pending
07:46:06 5m error ratio=16.8% alerts=TaskflowHighErrorRate=pending
07:46:21 5m error ratio=20.3% alerts=TaskflowHighErrorRate=pending
07:46:36 5m error ratio=20.3% alerts=TaskflowHighErrorRate=firing
== 07:46:36 Alertmanager received:
  TaskflowHighErrorRate critical active since 2026-10-17T07:46:28.966Z | More than 5% of TaskFlow API requests are failing | https://github.com/hemkeshkantawala11/taskflow/blob/devops/platform/docs/runbook.md#taskflowhigherrorrate
== 500s by route (5m):
  /api/tasks 1085
== 07:50:36 errors OFF
scripts/demo.sh errors-off
[devops/platform 88cf1e8] demo: set chaosErrorRate="0" [skip ci]
07:50:42 5m error ratio=30.0% alerts=TaskflowHighErrorRate=firing
07:50:58 5m error ratio=29.5% alerts=TaskflowHighErrorRate=firing
07:51:13 5m error ratio=29.5% alerts=TaskflowHighErrorRate=firing,TaskflowRolloutStuck=pending
07:51:28 5m error ratio=28.3% alerts=TaskflowHighErrorRate=firing,TaskflowRolloutStuck=pending
07:51:43 5m error ratio=28.3% alerts=TaskflowHighErrorRate=firing
07:51:58 5m error ratio=24.1% alerts=TaskflowHighErrorRate=firing
07:52:13 5m error ratio=24.1% alerts=TaskflowHighErrorRate=firing
07:52:28 5m error ratio=21.3% alerts=TaskflowHighErrorRate=firing
07:52:43 5m error ratio=21.3% alerts=TaskflowHighErrorRate=firing
07:52:58 5m error ratio=18.7% alerts=TaskflowHighErrorRate=firing
07:53:14 5m error ratio=18.7% alerts=TaskflowHighErrorRate=firing
07:53:29 5m error ratio=15.4% alerts=TaskflowHighErrorRate=firing
07:53:44 5m error ratio=15.4% alerts=TaskflowHighErrorRate=firing
07:53:59 5m error ratio=12.3% alerts=TaskflowHighErrorRate=firing
07:54:14 5m error ratio=12.3% alerts=TaskflowHighErrorRate=firing
07:54:29 5m error ratio=9.6% alerts=TaskflowHighErrorRate=firing
07:54:44 5m error ratio=9.6% alerts=TaskflowHighErrorRate=firing
07:54:59 5m error ratio=6.8% alerts=TaskflowHighErrorRate=firing
07:55:14 5m error ratio=6.8% alerts=TaskflowHighErrorRate=firing
07:55:29 5m error ratio=4.1% alerts=none
```

Reading it: the ratio rises as new pods (rolled by the config change) take traffic; the alert is
*pending* once above 5% and *fires* after 2 minutes; Alertmanager receives it with severity, summary
and runbook link. After the errors are switched off the 5-minute window drains and the alert resolves when it
drops below 5%. `TaskflowRolloutStuck=pending` appears briefly during each config rollout and clears.
