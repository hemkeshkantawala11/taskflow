# Autoscaling under load (release ea5c829)

`make load` (~25 req/s) pushed CPU above the HPA target (70% of the 50m request), so the
HPA scaled the web Deployment from 2 to its maximum of 5. Captured 2026-10-13 19:20 UTC.

```
NAME       REFERENCE             TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
taskflow   Deployment/taskflow   cpu: 102%/70%   2         5         5          48m

TIME                   REASON                  MESSAGE
2026-10-13T18:32:41Z   SuccessfulRescale       New size: 2; reason: Current number of replicas below Spec.MinReplicas
2026-10-13T19:04:02Z   SuccessfulRescale              New size: 3; reason: cpu resource utilization (percentage of request) above target
2026-10-13T19:07:17Z   SuccessfulRescale              New size: 4; reason: cpu resource utilization (percentage of request) above target
2026-10-13T19:09:33Z   SuccessfulRescale              New size: 5; reason: cpu resource utilization (percentage of request) above target

NAME                       READY  STATUS   AGE  NODE
taskflow-744b857c74-8wqxj  1/1    Running  16m  taskflow-worker2
taskflow-744b857c74-bz892  1/1    Running  19m  taskflow-worker
taskflow-744b857c74-pkq6w  1/1    Running  18m  taskflow-worker
taskflow-744b857c74-r6977  1/1    Running  11m  taskflow-worker
taskflow-744b857c74-spk2q  1/1    Running  13m  taskflow-worker2
```

At 5 pods and still above target, the HPA is at its ceiling: the next limits would be
maxReplicas and the database (5 pods x pool of 5 = 25 connections).
