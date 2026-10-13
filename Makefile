# Common tasks. Run `make help` to list them.
.DEFAULT_GOAL := help
SHELL := /bin/bash

help: ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[1m%-14s\033[0m %s\n", $$1, $$2}'

# ---------- local development ----------
dev: ## Run app + Postgres + Jaeger with Docker Compose (no Kubernetes)
	docker compose up --build

test: ## Lint and run tests (needs a Postgres; easiest: `docker compose up db`)
	DB_USER=taskflow DB_PASSWORD=local-dev-only DB_NAME=taskflow \
	  bash -c "ruff check . && ruff format --check . && pytest --cov=app"

# ---------- cluster ----------
cluster: ## Create kind cluster and install the whole platform (idempotent)
	scripts/setup-cluster.sh

status: ## What is running, and which version
	@kubectl -n argocd get application taskflow -o jsonpath='Argo CD: sync={.status.sync.status} health={.status.health.status} revision={.status.sync.revision}{"\n"}' || true
	@kubectl -n taskflow get pods,hpa,ingress -o wide
	@echo; curl -s http://taskflow.localtest.me:8080/version; echo

sync: ## Ask Argo CD to re-check Git now instead of waiting for the poll
	kubectl -n argocd annotate application taskflow argocd.argoproj.io/refresh=normal --overwrite

smoke: ## User-journey test through the ingress
	scripts/smoke-test.sh

verify: ## Collect end-to-end evidence into evidence/
	scripts/verify.sh

ui: ## Port-forward the tool UIs (Ctrl-C to stop)
	@echo "Grafana      http://localhost:3000   (admin / see create-secrets output)"
	@echo "Argo CD      http://localhost:8081   (admin / make argocd-password)"
	@echo "Prometheus   http://localhost:9090"
	@echo "Alertmanager http://localhost:9093"
	@echo "Jaeger       http://localhost:16686"
	@trap 'kill 0' INT; \
	kubectl -n monitoring port-forward svc/kps-grafana 3000:80 >/dev/null & \
	kubectl -n argocd port-forward svc/argocd-server 8081:80 >/dev/null & \
	kubectl -n monitoring port-forward svc/kps-kube-prometheus-stack-prometheus 9090:9090 >/dev/null & \
	kubectl -n monitoring port-forward svc/kps-kube-prometheus-stack-alertmanager 9093:9093 >/dev/null & \
	kubectl -n observability port-forward svc/jaeger 16686:16686 >/dev/null & \
	wait

grafana-password: ## Print the Grafana admin password
	@kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d; echo

argocd-password: ## Print the initial Argo CD admin password
	@kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo

# ---------- release control ----------
rollback: ## Roll back the last release the GitOps way (revert the newest deploy commit)
	@c=$$(git log --format=%H --grep='^deploy(local):' -1); \
	 [ -n "$$c" ] || { echo "no deploy commit found"; exit 1; }; \
	 git log -1 --format='Reverting %h %s' $$c; \
	 git revert --no-edit $$c && git push

# ---------- failure demos (see docs/fault-demo.md) ----------
load: ## Generate steady traffic
	scripts/demo.sh load
demo-drift: ## Manual change -> Argo CD self-heals it
	scripts/demo.sh drift
demo-db: ## Kill the database pod -> recovers, data persists
	scripts/demo.sh db-down
demo-bad-release: ## Ship an image that can't start -> old pods keep serving
	scripts/demo.sh bad-release
demo-errors-on: ## Inject 30% API errors -> SLO alerts fire
	scripts/demo.sh errors-on
demo-errors-off: ## Remove injected errors -> alerts resolve
	scripts/demo.sh errors-off

clean: ## Delete the kind cluster
	kind delete cluster --name taskflow

.PHONY: help dev test cluster status sync smoke verify ui grafana-password argocd-password rollback load demo-drift demo-db demo-bad-release demo-errors-on demo-errors-off clean
