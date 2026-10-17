#!/usr/bin/env bash
# Creates the local kind cluster and installs the platform: ingress, metrics,
# monitoring, logging, tracing and Argo CD. Idempotent: safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
source deploy/platform/versions.env
P=deploy/platform

for tool in docker kind kubectl helm openssl; do
  command -v "$tool" >/dev/null || { echo "Missing prerequisite: $tool (see README)"; exit 1; }
done

step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

step "Cluster"
if kind get clusters | grep -qx taskflow; then
  echo "kind cluster 'taskflow' already exists"
else
  kind create cluster --config deploy/kind/cluster.yaml --wait 120s
fi
kubectl config use-context kind-taskflow >/dev/null

step "Namespaces and secrets"
kubectl apply -f $P/namespaces.yaml
scripts/create-secrets.sh

step "Helm repositories"
helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null
helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update >/dev/null

step "metrics-server (for the HPA)"
helm upgrade --install metrics-server metrics-server/metrics-server --version "$METRICS_SERVER_CHART" \
  -n kube-system -f $P/metrics-server-values.yaml --wait

step "Traefik ingress controller"
helm upgrade --install traefik traefik/traefik --version "$TRAEFIK_CHART" \
  -n traefik -f $P/traefik-values.yaml --wait

step "Prometheus, Alertmanager, Grafana (kube-prometheus-stack) - takes a few minutes"
helm upgrade --install kps prometheus-community/kube-prometheus-stack --version "$KPS_CHART" \
  -n monitoring -f $P/kube-prometheus-stack-values.yaml --wait --timeout 10m

step "Loki + Alloy (logs) and Jaeger (traces)"
helm upgrade --install loki grafana/loki --version "$LOKI_CHART" \
  -n observability -f $P/loki-values.yaml --wait --timeout 10m
helm upgrade --install alloy grafana/alloy --version "$ALLOY_CHART" \
  -n observability -f $P/alloy-values.yaml --wait
kubectl apply -f $P/jaeger.yaml
kubectl -n observability rollout status deploy/jaeger --timeout 180s

step "Argo CD"
helm upgrade --install argocd argo/argo-cd --version "$ARGOCD_CHART" \
  -n argocd -f $P/argocd-values.yaml --wait --timeout 10m
kubectl apply -f deploy/argocd/project.yaml -f deploy/argocd/application.yaml

step "Done"
cat <<MSG
Argo CD now deploys TaskFlow from Git. The first sync only succeeds after CI has
pushed an image and committed its tag (see README, "First release").

  make status   # what is running
  make ui       # port-forward Grafana, Argo CD, Prometheus, Alertmanager, Jaeger
  make verify   # end-to-end evidence: commit -> image -> pods -> user request
MSG
