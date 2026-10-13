#!/usr/bin/env bash
# Failure scenarios for the viva. Each prints what to watch. See docs/fault-demo.md.
set -euo pipefail
cd "$(dirname "$0")/.."
BASE=${BASE_URL:-http://taskflow.localtest.me:8080}
VALUES=deploy/helm/taskflow/values-local.yaml

case "${1:-}" in
  load)       # steady traffic so dashboards and alerts have data
    echo "Sending traffic to $BASE (Ctrl-C to stop)"
    while true; do
      curl -s -o /dev/null -X POST "$BASE/api/tasks" -H 'Content-Type: application/json' -d '{"title":"load"}'
      for _ in 1 2 3 4; do curl -s -o /dev/null "$BASE/api/tasks"; done
      sleep 0.2
    done ;;

  drift)      # change the cluster by hand; Argo CD's selfHeal puts it back
    kubectl -n taskflow set env deploy/taskflow LOG_LEVEL=DEBUG
    echo "Manual change applied. Watch Argo CD revert it (usually < 1 min):"
    echo "  kubectl -n taskflow get deploy taskflow -o jsonpath='{.spec.template.spec.containers[0].env}' ; echo"
    echo "  kubectl -n argocd get application taskflow -w" ;;

  db-down)    # kill the database pod; StatefulSet recreates it, PVC keeps the data
    curl -s -X POST "$BASE/api/tasks" -H 'Content-Type: application/json' -d '{"title":"survives a DB restart"}'; echo
    kubectl -n taskflow delete pod taskflow-postgres-0 --wait=false
    echo "Watch app pods turn NotReady then Ready again, and the task still exist afterwards:"
    echo "  kubectl -n taskflow get pods -w" ;;

  bad-release) # release an image that cannot start; old pods keep serving
    sed -i -E 's|^(  tag: ).*|\1"does-not-exist"|' $VALUES
    git commit -am "release: deliberately broken image tag (fault demo) [skip ci]"
    git push
    echo "Watch: new pod ImagePullBackOff, old pods still Ready (maxUnavailable: 0)."
    echo "Recover with:  git revert --no-edit HEAD && git push" ;;

  errors-on|errors-off)  # inject 30% API failures through Git -> alerts fire / clear
    rate=$([ "$1" = errors-on ] && echo '"0.3"' || echo '"0"')
    python3 - "$VALUES" "$rate" <<'PY'
import re, sys
path, rate = sys.argv[1], sys.argv[2]
text = open(path).read()
text = re.sub(r'\napp:\n  chaosErrorRate: .*\n', '\n', text)
if rate != '"0"':
    text = text.rstrip('\n') + f'\napp:\n  chaosErrorRate: {rate}\n'
open(path, 'w').write(text)
PY
    git commit -am "demo: set chaosErrorRate=$rate [skip ci]"
    git push
    echo "Argo CD syncs in ~1 min. Run 'scripts/demo.sh load' and watch the Grafana dashboard + alerts." ;;

  *) echo "usage: $0 {load|drift|db-down|bad-release|errors-on|errors-off}"; exit 1 ;;
esac
