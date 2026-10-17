#!/usr/bin/env python3
"""Turn a rendered PrometheusRule into a plain Prometheus rules file for promtool.

Usage:
  helm template taskflow deploy/helm/taskflow \
    -f deploy/helm/taskflow/values-local.yaml \
    --show-only templates/prometheusrule.yaml \
    | python3 scripts/extract-rules.py > deploy/tests/rules.yaml

Standard library only (no PyYAML), so it runs on any CI runner: it prints the
indented block under the top-level `spec:` key, de-indented by two spaces.
"""

import sys

lines = sys.stdin.read().splitlines()
try:
    start = lines.index("spec:") + 1
except ValueError:
    sys.exit("no top-level 'spec:' found - pass the rendered PrometheusRule only")

for line in lines[start:]:
    if line and not line.startswith("  "):  # next top-level key or document marker
        break
    print(line[2:])
