# TaskFlow verification - 2026-10-17 07:58 UTC

## 1. Source (Git)
```
9f28e3a Hemkesh Kantawala 2026-10-17 Revert "release: deliberately broken image tag (fault demo) [skip ci]"
8417ea0 Hemkesh Kantawala 2026-10-17 release: deliberately broken image tag (fault demo) [skip ci]
88cf1e8 Hemkesh Kantawala 2026-10-17 demo: set chaosErrorRate="0" [skip ci]

values-local.yaml image tag:   tag: "a0f7b71eea781c3ebc1d42b08e8a63d43281afd5"
```

## 2. Delivery (Argo CD)
```
synced revision: 9f28e3afdb8e9717873fd27ca0809b3fbb6ffd81
sync: Synced
health: Healthy
```

## 3. Runtime (Kubernetes)
```
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/taskflow   5/5     5            5           3d13h

NAME                                 READY   AGE
statefulset.apps/taskflow-postgres   1/1     3d13h

NAME                                           REFERENCE             TARGETS        MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/taskflow   Deployment/taskflow   cpu: 61%/70%   2         5         5          3d13h

NAME                                  MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE
poddisruptionbudget.policy/taskflow   1               N/A               4                     3d13h

NAME                                 CLASS     HOSTS                   ADDRESS     PORTS   AGE
ingress.networking.k8s.io/taskflow   traefik   taskflow.localtest.me   127.0.0.1   80      3d13h

NAME                                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-taskflow-postgres-0   Bound    pvc-111ea0d7-0d13-4007-9b27-ec2fe1a39974   1Gi        RWO            standard       <unset>                 3d13h

NAME                      READY   STATUS    RESTARTS   AGE     IP            NODE               NOMINATED NODE   READINESS GATES
taskflow-c6545448-49mms   1/1     Running   0          8m6s    10.244.1.26   taskflow-worker    <none>           <none>
taskflow-c6545448-cp55m   1/1     Running   0          7m58s   10.244.1.27   taskflow-worker    <none>           <none>
taskflow-c6545448-lz676   1/1     Running   0          101s    10.244.1.29   taskflow-worker    <none>           <none>
taskflow-c6545448-t9jhn   1/1     Running   0          3m41s   10.244.2.25   taskflow-worker2   <none>           <none>
taskflow-c6545448-ts5k4   1/1     Running   0          8m14s   10.244.2.24   taskflow-worker2   <none>           <none>
taskflow-postgres-0       1/1     Running   0          77s     10.244.2.26   taskflow-worker2   <none>           <none>

Images running:
taskflow-c6545448-49mms  ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-cp55m  ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-lz676  ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-t9jhn  ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-ts5k4  ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-postgres-0  postgres:16-alpine

10        <none>
12        <none>
14        <none>
15        <none>

```

## 4. Running version as seen by users (/version, several requests)
```
{"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-49mms"}
{"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-t9jhn"}
{"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-cp55m"}
{"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-ts5k4"}
{"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-cp55m"}
{"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-ts5k4"}
```

## 5. User journey (smoke test through the ingress)
```
ok   web page loads
ok   created task 32854
ok   task listed
ok   task completed
ok   task deleted
Served by: {"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-t9jhn"}
SMOKE TEST PASSED
```

## 6. Signals
```
API availability over the last 5 minutes (SLO target: 99%):
100.000%
Firing or pending alerts:
none
```
