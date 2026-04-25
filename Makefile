.PHONY: help up down reset reset-docker reset-kind reset-all verify smoke kind-up kind-down kind-load logs ps scenarios operator-up operator-shell operator-down operator-recon proctor-url proctor-reset

CLUSTER_NAME := forge-range
KIND_CONFIG  := kind/cluster.yaml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Bring up Docker Compose lab environment
	docker compose up -d
	@echo "Lab is up. Run 'make verify' to check services."

down: ## Stop Docker Compose lab environment
	docker compose down

reset: ## Destroy and rebuild the entire lab
	docker compose down -v --remove-orphans
	docker compose up -d --build
	@echo "Lab reset complete."

reset-docker: ## Fully reset Docker Compose state and rebuild containers
	docker compose down -v --remove-orphans
	docker compose up -d --build
	@echo "Docker lab state reset complete."

reset-kind: ## Destroy the local kind cluster if it exists
	@if kind get clusters | grep -qx "$(CLUSTER_NAME)"; then \
		kind delete cluster --name $(CLUSTER_NAME); \
		echo "kind cluster $(CLUSTER_NAME) deleted."; \
	else \
		echo "kind cluster $(CLUSTER_NAME) not present; nothing to delete."; \
	fi

reset-all: reset-docker reset-kind ## Fully reset Docker Compose and kind state
	@echo "Docker and kind state reset complete."

verify: ## Run full connectivity and safety checks against lab services
	@bash scripts/verify.sh

smoke: ## Run quick smoke tests (service reachability and safety boundaries)
	@bash scripts/smoke.sh

logs: ## Follow Docker Compose logs for all services
	docker compose logs -f

ps: ## Show status of all lab containers
	docker compose ps

kind-up: ## Create local kind Kubernetes cluster
	kind create cluster --name $(CLUSTER_NAME) --config $(KIND_CONFIG)
	kubectl cluster-info --context kind-$(CLUSTER_NAME)

kind-down: ## Destroy kind Kubernetes cluster
	kind delete cluster --name $(CLUSTER_NAME)

kind-load: ## Load local Docker images into kind cluster
	@for img in $$(docker compose config --images); do \
		echo "Loading $$img into kind..."; \
		kind load docker-image $$img --name $(CLUSTER_NAME); \
	done

operator-up: ## Start the operator container (internal enumeration, no exposed ports)
	docker compose up -d operator

operator-shell: ## Open a shell in the operator container
	docker exec -it forge-operator bash

operator-down: ## Remove the operator container
	docker compose rm -sf operator

operator-recon: ## Run the baseline recon script inside the operator container
	docker exec forge-operator /bin/bash /scripts/operator-recon.sh

proctor-url: ## Print the local Proctor scoring UI URL
	@echo "Forge Proctor: http://127.0.0.1:8090"

proctor-reset: ## Reset Proctor — wipes all scores and accounts, keeps other lab state
	docker compose stop proctor
	docker volume rm forge-range_proctor_data || true
	docker compose up -d proctor

scenarios: ## List available attack scenarios
	@echo ""
	@echo "Available scenarios:"
	@for d in scenarios/*/; do \
		name=$$(basename $$d); \
		desc=$$(head -n 2 $$d/README.md 2>/dev/null | tail -n 1); \
		printf "  \033[36m%-30s\033[0m %s\n" "$$name" "$$desc"; \
	done
	@echo ""
