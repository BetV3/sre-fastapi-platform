.PHONY: help install dev run test lint format docker-build docker-up docker-down docker-logs clean

# Default target
help:
	@echo "FastAPI Platform - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "Development:"
	@echo "  install     Install production dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  run         Run the application locally"
	@echo "  test        Run tests with coverage"
	@echo "  lint        Run linters (ruff)"
	@echo "  format      Format code (ruff)"
	@echo "  typecheck   Run type checker (mypy)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    Build Docker images"
	@echo "  docker-up       Start all services"
	@echo "  docker-down     Stop all services"
	@echo "  docker-logs     View logs from all services"
	@echo "  docker-restart  Restart all services"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean       Remove cache files and build artifacts"

# Development
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install ruff mypy pytest pytest-asyncio pytest-cov httpx

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

lint:
	ruff check app/ tests/

format:
	ruff check --fix app/ tests/
	ruff format app/ tests/

typecheck:
	mypy app/

# Docker
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-restart:
	docker compose down
	docker compose up -d

docker-clean:
	docker compose down -v --rmi local

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
