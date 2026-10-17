# Bad release and rollback (release a0f7b71)

`make demo-bad-release` commits an image tag that does not exist (`8417ea0`, `[skip ci]`); Argo CD
applies it. Recovery is a Git revert (`9f28e3a`), so the rollback is reviewed and recorded like any
other change. `make load` ran throughout.

```
== 07:56:03 bad release
[devops/platform 8417ea0] release: deliberately broken image tag (fault demo) [skip ci]
07:56:10 argo=Synced/Healthy@88cf1e8a2639810 bad-pods=0
07:56:15 argo=Synced/Progressing@8417ea03704 bad-pods=0
07:56:20 argo=Synced/Progressing@8417ea03704 bad-pods=1
== 07:56:40 during the bad release:
NAME                        READY   STATE              IMAGE
taskflow-85cfb444d8-6qsvb   false   ImagePullBackOff   does-not-exist
taskflow-c6545448-49mms     true    <none>             a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-cp55m     true    <none>             a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-t9jhn     true    <none>             a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-c6545448-ts5k4     true    <none>             a0f7b71eea781c3ebc1d42b08e8a63d43281afd5
taskflow-postgres-0         true    <none>             postgres:16-alpine
5s          Warning   Failed                         pod/taskflow-85cfb444d8-6qsvb      Failed to pull image "ghcr.io/hemkeshkantawala11/taskflow:does-not-exist": rpc error: code = NotFound desc = failed to pull and unpack image "ghcr.io/hemkeshkanta
== smoke test while broken:
Served by: {"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-t9jhn"}
SMOKE TEST PASSED
== 07:56:40 rollback: git revert
[devops/platform 9f28e3a] Revert "release: deliberately broken image tag (fault demo) [skip ci]"
07:56:46 argo=Synced/Progressing@8417ea03704 bad-pods=1
07:56:52 argo=OutOfSync/Progressing@9f28e3af bad-pods=1
07:56:57 argo=Synced/Healthy@9f28e3afdb8e971 bad-pods=0
== after rollback:
Served by: {"version":"1.0.13","git_sha":"a0f7b71eea781c3ebc1d42b08e8a63d43281afd5","build_time":"2026-10-17T07:36:24Z","pod":"taskflow-c6545448-49mms"}
SMOKE TEST PASSED
9f28e3a Hemkesh Kantawala | Revert "release: deliberately broken image tag (fault demo) [skip ci]"
8417ea0 Hemkesh Kantawala | release: deliberately broken image tag (fault demo) [skip ci]
88cf1e8 Hemkesh Kantawala | demo: set chaosErrorRate="0" [skip ci]
```

Real API traffic from `make load` over the whole demo window (Prometheus, 07:55:55-07:57:05):
**200: 856, 201: 206, 204: 0** - no request failed.

Why: `maxUnavailable: 0` keeps every old pod until a new one is Ready, and the new pod never
becomes Ready, so the rollout simply stops with the old version serving (`TaskflowRolloutStuck` would
fire after 5 minutes). Time from `git revert` to Synced/Healthy: 17 s.
