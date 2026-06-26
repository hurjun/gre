# Developer shortcuts. Run `make help` for the list.
# The backend targets use a project-local virtualenv at backend/.venv.

.DEFAULT_GOAL := help
.PHONY: help setup test lint format typecheck validate check seed sim backend frontend

VENV := backend/.venv
BIN := $(VENV)/bin

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Create the backend venv, install dev deps, and install frontend deps
	python3 -m venv $(VENV)
	$(BIN)/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

test: ## Run the backend test suite with coverage
	cd backend && .venv/bin/pytest --cov=app --cov-report=term-missing --cov-fail-under=75

lint: ## Check style and imports (ruff)
	cd backend && .venv/bin/ruff check app tests
	cd backend && .venv/bin/ruff format --check app tests

format: ## Auto-format the backend (ruff)
	cd backend && .venv/bin/ruff format app tests

typecheck: ## Static type check (mypy)
	cd backend && .venv/bin/mypy

validate: ## Validate the JSON content bank (no database needed)
	cd backend && .venv/bin/python -m app.seed.validate

check: lint typecheck validate test ## Run the full local CI equivalent

seed: ## Seed the database from the JSON content bank
	cd backend && .venv/bin/python -m app.seed.seed

sim: ## Print the adaptive-ladder convergence table
	cd backend && .venv/bin/python -m app.services.simulation

backend: ## Run the API server with autoreload
	cd backend && .venv/bin/uvicorn app.main:app --reload

frontend: ## Run the Vite dev server
	cd frontend && npm run dev
