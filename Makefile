.PHONY: help install dev clean docker-up docker-down migrate test lint format

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development servers"
	@echo "  make docker-up    - Start all Docker services"
	@echo "  make docker-down  - Stop all Docker services"
	@echo "  make migrate      - Run database migrations"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"

install:
	@echo "Installing Python dependencies..."
	poetry install --no-root
	@echo "Installing Node dependencies..."
	pnpm install

dev:
	@echo "Starting development environment..."
	@make docker-up
	@echo "Starting FastAPI..."
	cd apps/api && poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting Next.js..."
	cd apps/web && pnpm dev

docker-up:
	docker-compose -f infra/docker/docker-compose.dev.yml up -d

docker-down:
	docker-compose -f infra/docker/docker-compose.dev.yml down

migrate:
	cd apps/api && poetry run alembic upgrade head

test:
	@echo "Running Python tests..."
	poetry run pytest
	@echo "Running TypeScript tests..."
	pnpm test

lint:
	@echo "Linting Python..."
	poetry run ruff check .
	poetry run mypy .
	@echo "Linting TypeScript..."
	pnpm lint

format:
	@echo "Formatting Python..."
	poetry run black .
	poetry run ruff check --fix .
	@echo "Formatting TypeScript..."
	pnpm format

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

docker-logs:
	docker-compose -f infra/docker/docker-compose.dev.yml logs -f

docker-status:
	docker-compose -f infra/docker/docker-compose.dev.yml ps

docker-clean:
	docker-compose -f infra/docker/docker-compose.dev.yml down -v
	docker system prune -f

services-check:
	./infra/docker/check-services.sh	

migrate-create:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

migrate-up:
	cd apps/api && alembic upgrade head

migrate-down:
	cd apps/api && alembic downgrade -1

migrate-history:
	cd apps/api && alembic history

db-reset:
	make docker-down
	make docker-up
	sleep 5
	make migrate-up	
api-dev:
	cd apps/api && poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

api-prod:
	cd apps/api && poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

api-test:
	curl http://localhost:8000/health
	curl http://localhost:8000/health/db	
web-install:
	cd apps/web && pnpm install

web-dev:
	cd apps/web && pnpm dev

web-build:
	cd apps/web && pnpm build

full-dev:
	make docker-up
	sleep 5
	make api-dev &
	make web-dev	