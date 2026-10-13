#!/usr/bin/env bash
# The user journey, through the real entry point (Traefik ingress):
# open the page, create a task, see it listed, complete it, delete it.
set -euo pipefail
BASE=${BASE_URL:-http://taskflow.localtest.me:8080}
fail() { echo "FAIL: $*"; exit 1; }
pass() { echo "ok   $*"; }

code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/") ; [ "$code" = 200 ] || fail "GET / returned $code"
pass "web page loads"

title="smoke-$(date +%s)"
id=$(curl -sf -X POST "$BASE/api/tasks" -H 'Content-Type: application/json' \
      -d "{\"title\":\"$title\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])') \
  || fail "create task"
pass "created task $id"

curl -sf "$BASE/api/tasks" | grep -q "$title" || fail "task not listed"
pass "task listed"

curl -sf -X PATCH "$BASE/api/tasks/$id" -H 'Content-Type: application/json' -d '{"done":true}' \
  | grep -q '"done":true' || fail "complete task"
pass "task completed"

code=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/api/tasks/$id")
[ "$code" = 204 ] || fail "delete returned $code"
pass "task deleted"

echo "Served by: $(curl -sf "$BASE/version")"
echo "SMOKE TEST PASSED"
