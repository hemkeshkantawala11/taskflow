# Release history: commit → pipeline → approval → release commit → rollout

Every release went through the same path. Approvals come from the GitHub API
(`/actions/runs/<id>/approvals`); release commits are written by the deploy job; rollout
timelines were recorded from the cluster every 5 s, with `/version` requested ~5×/s throughout.

| # | Source commit | Pipeline run (push) | Approval | Release commit | Notes |
|---|---|---|---|---|---|
| 1 | [`4ca1851`](https://github.com/hemkeshkantawala11/taskflow/commit/4ca1851) | [38444226621](https://github.com/hemkeshkantawala11/taskflow/actions/runs/38444226621) | approved by hemkeshkantawala11 | [`677aa86`](https://github.com/hemkeshkantawala11/taskflow/commit/677aa86) | first release; replaced pods stuck on the placeholder tag |
| 2 | [`c03d002`](https://github.com/hemkeshkantawala11/taskflow/commit/c03d002) | [38449095615](https://github.com/hemkeshkantawala11/taskflow/actions/runs/38449095615) | approved by hemkeshkantawala11 | [`bb4b0ba`](https://github.com/hemkeshkantawala11/taskflow/commit/bb4b0ba) | tracing fix |
| 3 | [`ea5c829`](https://github.com/hemkeshkantawala11/taskflow/commit/ea5c829) | [38450569801](https://github.com/hemkeshkantawala11/taskflow/actions/runs/38450569801) | approved by hemkeshkantawala11 | [`55e7298`](https://github.com/hemkeshkantawala11/taskflow/commit/55e7298) | ops and platform fixes |
| 4 | [`28bb5ba`](https://github.com/hemkeshkantawala11/taskflow/commit/28bb5ba) | [38457615282](https://github.com/hemkeshkantawala11/taskflow/actions/runs/38457615282) | approved by hemkeshkantawala11 | [`2c6bea4`](https://github.com/hemkeshkantawala11/taskflow/commit/2c6bea4) | dashboard fix |
| 5 | [`654c9d0`](https://github.com/hemkeshkantawala11/taskflow/commit/654c9d0) | [39012923583](https://github.com/hemkeshkantawala11/taskflow/actions/runs/39012923583) | approved by hemkeshkantawala11 | [`aca413e`](https://github.com/hemkeshkantawala11/taskflow/commit/aca413e) | bounded list endpoint, drift demo fix |
| 6 | [`a0f7b71`](https://github.com/hemkeshkantawala11/taskflow/commit/a0f7b71) | [39014215134](https://github.com/hemkeshkantawala11/taskflow/actions/runs/39014215134) | approved by hemkeshkantawala11 | [`7cce9cb`](https://github.com/hemkeshkantawala11/taskflow/commit/7cce9cb) | fault injection counted by the SLO; **evidence version** |

## Release commit written by the pipeline (release 6)
```
commit 7cce9cbc0b95e11075d1e33e91fc75895018187e
Author: taskflow-release-bot

deploy(local): taskflow a0f7b71 [skip ci]

Image: ghcr.io/hemkeshkantawala11/taskflow:a0f7b71eea781c3ebc1d42b08e8a63d43281afd5

Source commit: a0f7b71eea781c3ebc1d42b08e8a63d43281afd5

Pipeline run: https://github.com/hemkeshkantawala11/taskflow/actions/runs/39014215134
```

## Zero-downtime rollouts

`maxSurge: 1`, `maxUnavailable: 0`, readiness gating, `minReadySeconds: 5` and `preStop` together mean
a new pod must be Ready before an old one is removed, and old pods stop receiving traffic before they exit.

Across the five recorded rollouts: **5247 requests, 0 failed.**

### Release 6

Traffic during rollout: 494 requests: HTTP 200 x494; 654c9d0 x265; a0f7b71 x229

```
07:40:29Z img=654c9d0eeb98936e50f2ec6a298fc73075905a67 argo=Synced/Healthy rev=a0f7b71 pods=[62c8p:1/1:Running 6lbt6:1/1:Running ]
07:41:00Z img=654c9d0eeb98936e50f2ec6a298fc73075905a67 argo=Synced/Healthy rev=a0f7b71 pods=[2dkqt:0/1:ContainerCreating 62c8p:1/1:Running 6lbt6:1/1:Running ]
07:41:05Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[2dkqt:1/1:Running 62c8p:1/1:Running 6lbt6:1/1:Running pqmc4:0/1:ContainerCreating ]
07:41:16Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[2dkqt:1/1:Running 62c8p:1/1:Running 6lbt6:1/1:Running pqmc4:1/1:Running ]
07:41:21Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[2dkqt:1/1:Terminating 62c8p:1/1:Running 6lbt6:1/1:Running mj995:0/1:ContainerCreating pqmc4:1/1:Running ]
07:41:26Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[62c8p:1/1:Running 6lbt6:1/1:Running mj995:0/1:ContainerCreating pqmc4:1/1:Running ]
07:41:31Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[62c8p:1/1:Running 6lbt6:1/1:Running mj995:1/1:Running pqmc4:1/1:Running ]
07:41:36Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[62c8p:1/1:Running 6lbt6:1/1:Terminating jp9lr:0/1:Running mj995:1/1:Running pqmc4:1/1:Running ]
07:41:41Z img=a0f7b71 argo=Synced/Progressing rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[62c8p:1/1:Running jp9lr:1/1:Running mj995:1/1:Running pqmc4:1/1:Running ]
07:41:47Z img=a0f7b71 argo=Synced/Healthy rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[62c8p:1/1:Terminating jp9lr:1/1:Running mj995:1/1:Running pqmc4:1/1:Running ]
07:41:52Z img=a0f7b71 argo=Synced/Healthy rev=7cce9cbc0b95e11075d1e33e91fc75895018187e pods=[jp9lr:1/1:Running mj995:1/1:Running pqmc4:1/1:Running ]
07:41:52Z ROLLOUT COMPLETE updated/ready/replicas=3/3/3
```

### Release 5

Traffic during rollout: 283 requests: HTTP 200 x283; 28bb5ba x92; 654c9d0 x191

```
07:20:06Z img=28bb5ba7faf6b64f0d5d68029eeeb1a8e9a94b59 argo=Synced/Healthy rev=654c9d0 pods=[5rqpl:1/1:Running dvt29:1/1:Running ]
07:20:11Z img=654c9d0 argo=Synced/Progressing rev=aca413e5c2078570c8d2e2411ce4c162e07374a1 pods=[24flr:0/1:ContainerCreating 5rqpl:1/1:Running dvt29:1/1:Running ]
07:20:22Z img=654c9d0 argo=Synced/Progressing rev=aca413e5c2078570c8d2e2411ce4c162e07374a1 pods=[24flr:0/1:Running 5rqpl:1/1:Running dvt29:1/1:Running ]
07:20:27Z img=654c9d0 argo=Synced/Progressing rev=aca413e5c2078570c8d2e2411ce4c162e07374a1 pods=[24flr:1/1:Running jswkg:0/1:ContainerCreating 5rqpl:1/1:Terminating dvt29:1/1:Running ]
07:20:32Z img=654c9d0 argo=Synced/Progressing rev=aca413e5c2078570c8d2e2411ce4c162e07374a1 pods=[24flr:1/1:Running jswkg:1/1:Running 5rqpl:1/1:Terminating dvt29:1/1:Running ]
07:20:37Z img=654c9d0 argo=Synced/Healthy rev=aca413e5c2078570c8d2e2411ce4c162e07374a1 pods=[24flr:1/1:Running jswkg:1/1:Running dvt29:1/1:Terminating ]
07:20:42Z img=654c9d0 argo=Synced/Healthy rev=aca413e5c2078570c8d2e2411ce4c162e07374a1 pods=[24flr:1/1:Running jswkg:1/1:Running ]
07:20:42Z ROLLOUT COMPLETE updated/ready/replicas=2/2/2
```

### Release 4

Traffic during rollout: 3236 requests: HTTP 200 x3236; ea5c829 x3003; 28bb5ba x233; 

```
19:51:07Z img=ea5c829e041d83eef5cd88b678eaf8997c65ff13 argo=Synced/Healthy rev=28bb5ba pods=[8wqxj:1/1:Running bz892:1/1:Running pkq6w:1/1:Running r6977:1/1:Running spk2q:1/1:Running ]
20:02:08Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:0/1:ContainerCreating 8wqxj:1/1:Running bz892:1/1:Running pkq6w:1/1:Running r6977:1/1:Running spk2q:1/1:Running ]
20:02:18Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:0/1:Running 8wqxj:1/1:Running bz892:1/1:Running pkq6w:1/1:Running r6977:1/1:Running spk2q:1/1:Running ]
20:02:23Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:1/1:Running 8wqxj:1/1:Running bz892:1/1:Running pkq6w:1/1:Running r6977:1/1:Running spk2q:1/1:Running ]
20:02:28Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:1/1:Running qrz9v:0/1:ContainerCreating 8wqxj:1/1:Running bz892:1/1:Running pkq6w:1/1:Terminating r6977:1/1:Running spk2q:1/1:Running ]
20:02:33Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:1/1:Running qrz9v:1/1:Running 8wqxj:1/1:Running bz892:1/1:Running r6977:1/1:Running spk2q:1/1:Running ]
20:02:39Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:1/1:Running qrz9v:1/1:Running wc7ps:0/1:Running 8wqxj:1/1:Running bz892:1/1:Running r6977:1/1:Running spk2q:1/1:Terminating ]
20:02:44Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:1/1:Running qrz9v:1/1:Running wc7ps:1/1:Running 8wqxj:1/1:Running bz892:1/1:Running r6977:1/1:Running spk2q:0/1:Completed ]
20:02:49Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d8kdj:1/1:Running qrz9v:1/1:Running t97jw:1/1:Running wc7ps:1/1:Running 8wqxj:1/1:Running bz892:1/1:Running r6977:1/1:Terminating ]
20:02:54Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d2vtl:0/1:Running d8kdj:1/1:Running qrz9v:1/1:Running t97jw:1/1:Running wc7ps:1/1:Running 8wqxj:1/1:Running bz892:1/1:Terminating ]
20:02:59Z img=28bb5ba argo=Synced/Progressing rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d2vtl:1/1:Running d8kdj:1/1:Running qrz9v:1/1:Running t97jw:1/1:Running wc7ps:1/1:Running 8wqxj:1/1:Terminating ]
20:03:04Z img=28bb5ba argo=Synced/Healthy rev=2c6bea45a9038c67e2f6905ad0f8c384f51de3f8 pods=[d2vtl:1/1:Running d8kdj:1/1:Running qrz9v:1/1:Running t97jw:1/1:Running wc7ps:1/1:Running ]
20:03:04Z ROLLOUT COMPLETE updated/ready/replicas=5/5/5
```

### Release 3

Traffic during rollout: 799 requests: HTTP 200 x799; ea5c829 x171; c03d002 x628; 

```
18:59:27Z img=c03d0021f86e7aaff8cf92286f7df8b1c8e46202 argo=Synced/Healthy rev=ea5c829 pods=[9nrlz:1/1:Running m9p74:1/1:Running ]
19:01:40Z img=ea5c829 argo=Synced/Progressing rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[9nrlz:1/1:Running m9p74:1/1:Running bz892:0/1:ContainerCreating ]
19:01:51Z img=ea5c829 argo=Synced/Progressing rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[9nrlz:1/1:Running m9p74:1/1:Running bz892:1/1:Running ]
19:01:56Z img=ea5c829 argo=Synced/Progressing rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[9nrlz:1/1:Running m9p74:1/1:Terminating bz892:1/1:Running pkq6w:0/1:Running ]
19:02:01Z img=ea5c829 argo=Synced/Progressing rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[9nrlz:1/1:Running bz892:1/1:Running pkq6w:1/1:Running ]
19:02:06Z img=ea5c829 argo=Synced/Healthy rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[9nrlz:1/1:Terminating bz892:1/1:Running pkq6w:1/1:Running ]
19:02:06Z ROLLOUT COMPLETE 2/2/2
19:02:12Z img=ea5c829 argo=Synced/Healthy rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[bz892:1/1:Running pkq6w:1/1:Running ]
19:02:17Z img=ea5c829 argo=Synced/Degraded rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[bz892:1/1:Running pkq6w:1/1:Running ]
19:02:32Z img=ea5c829 argo=Synced/Healthy rev=55e7298740ae6fa470828491ce5568475cc62bf6 pods=[bz892:1/1:Running pkq6w:1/1:Running ]
```

### Release 2

Traffic during rollout: 435 requests: HTTP 200 x435; 4ca1851 x255; c03d002 x180; 

```
18:47:57Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Progressing rev=c03d002 pods=[tfl6q:1/1:Running twbgw:1/1:Running ]
18:48:28Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=OutOfSync/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Running twbgw:1/1:Running ]
18:48:33Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Running twbgw:1/1:Running m9p74:0/1:ContainerCreating ]
18:48:49Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Running twbgw:1/1:Running m9p74:0/1:Running ]
18:48:54Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Running twbgw:1/1:Terminating 9nrlz:0/1:ContainerCreating m9p74:1/1:Running ]
18:48:59Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Running twbgw:0/1:Completed 9nrlz:0/1:ContainerCreating m9p74:1/1:Running ]
18:49:05Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Running 9nrlz:1/1:Running m9p74:1/1:Running ]
18:49:10Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[tfl6q:1/1:Terminating 9nrlz:1/1:Running m9p74:1/1:Running ]
18:49:10Z ROLLOUT COMPLETE 2/2/2
18:49:15Z img=c03d002 argo=Synced/Degraded rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[9nrlz:1/1:Running m9p74:1/1:Running ]
18:49:30Z img=c03d002 argo=Synced/Progressing rev=bb4b0ba102f7873f56f5cfbf73af857fa192882c pods=[9nrlz:1/1:Running m9p74:1/1:Running ]
```

### Release 1

No traffic loop (pods were not serving before it). Timeline:
```
18:36:06Z img=latest-not-deployed-yet argo=Synced/Degraded rev=4ca1851ff1e59bc0d901b5931be908904d4a9516 pods=[gdck5:0/1:ImagePullBackOff kq75c:0/1:ImagePullBackOff ]
18:36:11Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Degraded rev=677aa860c9c5c44a529c8954d86ee91d50ea6aba pods=[tfl6q:0/1:ContainerCreating gdck5:0/1:ImagePullBackOff kq75c:0/1:ImagePullBackOff ]
18:36:16Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Degraded rev=677aa860c9c5c44a529c8954d86ee91d50ea6aba pods=[tfl6q:0/1:ContainerCreating gdck5:0/1:ImagePullBackOff kq75c:0/1:ErrImagePull ]
18:36:26Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Degraded rev=677aa860c9c5c44a529c8954d86ee91d50ea6aba pods=[tfl6q:0/1:Running gdck5:0/1:ImagePullBackOff kq75c:0/1:ImagePullBackOff ]
18:36:32Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Degraded rev=677aa860c9c5c44a529c8954d86ee91d50ea6aba pods=[tfl6q:1/1:Running twbgw:0/1:ContainerCreating gdck5:0/1:ImagePullBackOff kq75c:0/1:Terminating ]
18:36:37Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Degraded rev=677aa860c9c5c44a529c8954d86ee91d50ea6aba pods=[tfl6q:1/1:Running twbgw:1/1:Running gdck5:0/1:ImagePullBackOff ]
18:36:42Z img=4ca1851ff1e59bc0d901b5931be908904d4a9516 argo=Synced/Degraded rev=677aa860c9c5c44a529c8954d86ee91d50ea6aba pods=[tfl6q:1/1:Running twbgw:1/1:Running ]
18:36:42Z ROLLOUT COMPLETE 2/2/2
```
