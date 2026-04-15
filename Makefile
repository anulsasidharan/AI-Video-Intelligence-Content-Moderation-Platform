.PHONY: dev dev-frontend dev-backend dev-worker \
        build push \
        test test-backend test-frontend lint \
        db-migrate db-revision \
        tf-plan tf-apply deploy \
        up down logs ps clean \
        k8s-apply k8s-delete k8s-status k8s-migrate \
        k8s-logs-backend k8s-logs-worker k8s-logs-frontend \
        k8s-rollout-backend k8s-rollout-worker k8s-rollout-frontend

# ── Local Development ─────────────────────────────────────────────────────────
dev:
	docker compose up --build

dev-d:
	docker compose up --build -d

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info

# ── Docker Compose helpers ────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v --remove-orphans

# ── Testing ───────────────────────────────────────────────────────────────────
test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest --tb=short -q

test-frontend:
	cd frontend && npm test -- --passWithNoTests

lint:
	cd backend && python -m ruff check . && python -m ruff format --check .
	cd frontend && npm run lint

# ── Database ──────────────────────────────────────────────────────────────────
db-migrate:
	cd backend && alembic upgrade head

db-revision:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# ── Docker Build ──────────────────────────────────────────────────────────────
build:
	docker compose build

push:
	docker compose push

# ── Infrastructure ────────────────────────────────────────────────────────────
tf-plan:
	cd terraform && terraform plan -var-file=environments/$(ENV).tfvars

tf-apply:
	cd terraform && terraform apply -var-file=environments/$(ENV).tfvars

deploy:
	@echo "Deploying to $(ENV)..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build
	docker compose -f docker-compose.yml -f docker-compose.prod.yml push

# ── Kubernetes ────────────────────────────────────────────────────────────────
# Usage: make k8s-apply TAG=v1.2.3 REGISTRY=REGION-docker.pkg.dev/PROJECT/REPO
TAG      ?= latest
REGISTRY ?= <GAR_REGISTRY>

k8s-apply:
	kubectl apply -f k8s/00-namespace.yaml
	kubectl apply -f k8s/01-rbac.yaml
	kubectl apply -f k8s/02-configmap.yaml
	@echo "⚠  Apply secrets separately: kubectl apply -f k8s/03-secrets.yaml"
	kubectl apply -f k8s/04-postgres.yaml
	kubectl apply -f k8s/05-redis.yaml
	kubectl apply -f k8s/07-backend.yaml
	kubectl apply -f k8s/08-worker.yaml
	kubectl apply -f k8s/09-frontend.yaml
	kubectl apply -f k8s/10-ingress.yaml
	kubectl apply -f k8s/11-network-policies.yaml
	kubectl apply -f k8s/12-hpa.yaml
	kubectl apply -f k8s/13-pdb.yaml

k8s-migrate:
	kubectl apply -f k8s/06-backend-migrate.yaml
	kubectl wait --for=condition=complete job/vidshield-db-migrate -n vidshield --timeout=300s
	kubectl logs -n vidshield job/vidshield-db-migrate

k8s-delete:
	kubectl delete -k k8s/ --ignore-not-found

k8s-status:
	@echo "=== Pods ===" && kubectl get pods -n vidshield -o wide
	@echo "=== Services ===" && kubectl get svc -n vidshield
	@echo "=== HPAs ===" && kubectl get hpa -n vidshield
	@echo "=== PVCs ===" && kubectl get pvc -n vidshield

k8s-logs-backend:
	kubectl logs -n vidshield deploy/vidshield-backend -f --all-containers

k8s-logs-worker:
	kubectl logs -n vidshield deploy/vidshield-worker -f --all-containers

k8s-logs-frontend:
	kubectl logs -n vidshield deploy/vidshield-frontend -f --all-containers

k8s-rollout-backend:
	kubectl set image deployment/vidshield-backend api=$(REGISTRY)/vidshield-backend:$(TAG) -n vidshield
	kubectl rollout status deployment/vidshield-backend -n vidshield

k8s-rollout-worker:
	kubectl set image deployment/vidshield-worker worker=$(REGISTRY)/vidshield-backend:$(TAG) -n vidshield
	kubectl rollout status deployment/vidshield-worker -n vidshield

k8s-rollout-frontend:
	kubectl set image deployment/vidshield-frontend frontend=$(REGISTRY)/vidshield-frontend:$(TAG) -n vidshield
	kubectl rollout status deployment/vidshield-frontend -n vidshield
