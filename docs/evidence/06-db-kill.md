# Database pod killed (release a0f7b71)

`make demo-db` creates a task, then deletes `taskflow-postgres-0`. `make load` ran throughout.

```
07:57:40 task created and pod deleted
07:57:34 http=200 argo=Synced/Healthy@9f28e3a alerts=none pods=[49mms:1/1:Running:r0 cp55m:1/1:Running:r0 lz676:1/1:Running:r0 t9jhn:1/1:Running:r0 ts5k4:1/1:Running:r0 0:1/1:Running:r0 ]
07:57:41 http=500 argo=Synced/Healthy@9f28e3a alerts=none pods=[49mms:1/1:Running:r0 cp55m:1/1:Running:r0 lz676:1/1:Running:r0 t9jhn:1/1:Running:r0 ts5k4:1/1:Running:r0 0:1/1:Terminating:r0 ]
07:57:43 http=200 argo=Synced/Healthy@9f28e3a alerts=none pods=[49mms:1/1:Running:r0 cp55m:1/1:Running:r0 lz676:1/1:Running:r0 t9jhn:1/1:Running:r0 ts5k4:1/1:Running:r0 0:1/1:Running:r0 ]
```

Timeline from Kubernetes events and the PostgreSQL log:

```
07:57:40.8  task 32615 created, pod deleted ("Stopping container postgres")
07:57:41    old instance: "database system was shut down"   (clean shutdown)
07:57:42    StatefulSet created taskflow-postgres-0 again (new pod UID 26d86044…)
07:57:42.9  new instance: "database system is ready to accept connections"
```

The database was unavailable for about 2 seconds.

- **Task created just before the kill, read back afterwards:** `{'id': 32615, 'title': 'survives a DB restart', 'done': False, 'created_at': '2026-10-17T07:57:40.798311+00:00'}`
- **API requests over the 90 s around the kill (Prometheus):** 200: 1089, 201: 250, 204: 0, 500: 0
- **`taskflow_db_up` (max over pods, 5 s steps):** `1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1`
- **Web pod restarts before → after:**
```
taskflow-c6545448-49mms   0
taskflow-c6545448-cp55m   0
taskflow-c6545448-lz676   0
taskflow-c6545448-t9jhn   0
taskflow-c6545448-ts5k4   0
→
taskflow-c6545448-49mms   0
taskflow-c6545448-cp55m   0
taskflow-c6545448-lz676   0
taskflow-c6545448-t9jhn   0
taskflow-c6545448-ts5k4   0
```

The StatefulSet recreates the pod under the same name and re-attaches the same PVC, so data
survives. Liveness (`/healthz`) does not check the database, so the web pods are not restarted;
readiness (`/readyz`) does, and with probes every 5 s and `failureThreshold: 2`, an outage this
short does not take pods out of the Service. A longer outage would mark them NotReady (no traffic)
and fire `TaskflowDatabaseUnreachable` after 1 minute.
