.PHONY: help up down migrate test lint clean logs shell

help:
	@echo "Available commands:"
	@echo "  make up              - Start all services with docker-compose"
	@echo "  make down            - Stop all services"
	@echo "  make migrate         - Run database migrations"
	@echo "  make test            - Run pytest tests"
	@echo "  make lint            - Run code linting (flake8)"
	@echo "  make clean           - Clean up generated files"
	@echo "  make logs            - Show logs from all services"
	@echo "  make shell           - Open a shell in the API container"
	@echo "  make seed            - Seed the database with sample data"

up:
	docker-compose up -d
	@echo "Services are starting. API will be available at http://localhost:8000"
	@echo "Admin UI will be available at http://localhost:8000/admin"

down:
	docker-compose down

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

test:
	docker-compose exec api pytest tests/ -v

lint:
	docker-compose exec api flake8 app/ tests/ --max-line-length=120

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f worker

logs-scheduler:
	docker-compose logs -f scheduler

shell:
	docker-compose exec api /bin/bash

seed:
	docker-compose exec api python -m app.scripts.seed_data

demo:
	@echo "Running demo workflow..."
	@echo "1. Ingesting trends from RSS feeds..."
	curl -X POST http://localhost:8000/api/trends/ingest
	@echo "\n2. Creating a campaign..."
	curl -X POST http://localhost:8000/api/campaigns \
		-H "Content-Type: application/json" \
		-d '{"name": "Demo Campaign", "objective": "Test", "start_date": "2025-01-01", "end_date": "2025-12-31"}'
	@echo "\n3. Creating a tracked link..."
	curl -X POST http://localhost:8000/api/links \
		-H "Content-Type: application/json" \
		-d '{"campaign_id": 1, "channel": "email", "long_url": "https://example.com/page"}'
	@echo "\nDemo workflow complete!"
