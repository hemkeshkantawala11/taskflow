#!/usr/bin/env bash
# Connects source -> pipeline -> image -> cluster -> user request, and saves
# the output to evidence/verification-<timestamp>.md for the submission.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
mkdir -p evidence
out="evidence/verification-$(date -u +%Y%m%dT%H%M%SZ).md"
BASE=${BASE_URL:-http://taskflow.localtest.me:8080}

{
echo "# TaskFlow verification - $(date -u +'%Y-%m-%d %H:%M UTC')"
echo
echo "## 1. Source (Git)"
echo '```'
git log -3 --format='%h %an %ad %s' --date=short
echo
echo "values-local.yaml image tag: $(grep -E '^  tag:' deploy/helm/taskflow/values-local.yaml)"
echo '```'
echo
echo "## 2. Delivery (Argo CD)"
echo '```'
kubectl -n argocd get application taskflow \
  -o jsonpath='synced revision: {.status.sync.revision}{"\n"}sync: {.status.sync.status}{"\n"}health: {.status.health.status}{"\n"}' 2>&1
echo '```'
echo
echo "## 3. Runtime (Kubernetes)"
echo '```'
kubectl -n taskflow get deploy,statefulset,hpa,pdb,ingress,pvc 2>&1
echo
kubectl -n taskflow get pods -o wide 2>&1
echo
echo "Images running:"
kubectl -n taskflow get pods -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.spec.containers[0].image}{"\n"}{end}' 2>&1
echo
kubectl -n taskflow rollout history deploy/taskflow 2>&1 | tail -5
echo '```'
echo
echo "## 4. Running version as seen by users (/version, several requests)"
echo '```'
for _ in 1 2 3 4 5 6; do curl -s "$BASE/version"; echo; done
echo '```'
echo
echo "## 5. User journey (smoke test through the ingress)"
echo '```'
scripts/smoke-test.sh 2>&1
echo '```'
echo
echo "## 6. Signals"
echo '```'
# Query Prometheus through the API server's service proxy: needs no tools inside
# the (minimal) Prometheus image and no port-forward.
prom() { kubectl get --raw "/api/v1/namespaces/monitoring/services/kps-kube-prometheus-stack-prometheus:9090/proxy/api/v1/$1"; }
echo "API availability over the last 5 minutes (SLO target: 99%):"
prom 'query?query=1-taskflow%3Aapi_error_ratio%3Arate5m' 2>&1 | python3 -c '
import json,sys
r=json.load(sys.stdin)["data"]["result"]
print(format(float(r[0]["value"][1]), ".3%") if r else "no data yet")' 2>&1
echo "Firing or pending alerts:"
prom 'alerts' 2>&1 | python3 -c '
import json,sys
a=[x for x in json.load(sys.stdin)["data"]["alerts"] if x["labels"].get("service")=="taskflow"]
print("\n".join(x["labels"]["alertname"] + ": " + x["state"] for x in a) or "none")' 2>&1
echo '```'
} | tee "$out"

echo
echo "Saved to $out"
