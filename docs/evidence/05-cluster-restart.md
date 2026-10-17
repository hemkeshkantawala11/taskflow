# Whole-cluster stop and restart

On 2026-10-14 08:30 UTC all three kind node containers were stopped with `docker stop`
(`docker events`: stop signal 37, then 9, for each node in turn; not an OOM kill). They stayed
stopped for ~3 days and were started again on 2026-10-17 06:58:56 UTC:

```
docker start taskflow-control-plane taskflow-worker taskflow-worker2
```

State at 07:07 UTC (first check after start, ~9 minutes later; the exact recovery time was
not measured):

```
NAME                     STATUS   ROLES           AGE     VERSION
taskflow-control-plane   Ready    control-plane   3d12h   v1.37.0
taskflow-worker          Ready    <none>          3d12h   v1.37.0
taskflow-worker2         Ready    <none>          3d12h   v1.37.0

Argo CD: Synced/Healthy at 2c6bea45a9038c67e2f6905ad0f8c384f51de3f8
Platform pods not Running: 0 of 34

NAME                        READY   RESTARTS   NODE
taskflow-5b74fcfc96-d8kdj   true    2          taskflow-worker2
taskflow-5b74fcfc96-wc7ps   true    2          taskflow-worker2
taskflow-postgres-0         true    2          taskflow-worker2

GET /version -> {"version":"1.0.7","git_sha":"28bb5ba7faf6b64f0d5d68029eeeb1a8e9a94b59","build_time":"2026-10-13T19:47:59Z","pod":"taskflow-5b74fcfc96-d8kdj"}
Tasks still in the database: 26483
```

What this shows: desired state (Argo CD, Deployments, StatefulSet) and data (PVC on the
node's disk) survive a full cluster stop. The HPA had scaled back to its minimum of 2.
