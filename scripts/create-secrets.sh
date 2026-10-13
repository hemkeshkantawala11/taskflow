#!/usr/bin/env bash
# Generates credentials directly inside the cluster. They are never written to
# disk or committed to Git. Re-running keeps existing secrets (no surprise rotation).
set -euo pipefail

create() {  # namespace name key=value...
  local ns=$1 name=$2; shift 2
  if kubectl -n "$ns" get secret "$name" >/dev/null 2>&1; then
    echo "secret $ns/$name exists - keeping it"
    return
  fi
  local args=()
  for kv in "$@"; do args+=(--from-literal="$kv"); done
  kubectl -n "$ns" create secret generic "$name" "${args[@]}" >/dev/null
  echo "secret $ns/$name created"
}

create taskflow taskflow-db username=taskflow "password=$(openssl rand -hex 24)"
create monitoring grafana-admin admin-user=admin "admin-password=$(openssl rand -hex 16)"

cat <<'MSG'
Grafana login: user "admin", password via
  kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d; echo
If your GHCR package is private, also create a pull secret (token with read:packages only):
  kubectl -n taskflow create secret docker-registry ghcr-pull --docker-server=ghcr.io \
    --docker-username=<github-user> --docker-password=<token>
and set imagePullSecrets: [{name: ghcr-pull}] in values-local.yaml.
MSG
