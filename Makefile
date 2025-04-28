all: down build up

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

fmt:
	uv run ruff check --select I --fix .
	uv run ruff format

lint:
	uv run ruff check

checks: fmt lint

requirements:
	uv export --no-group dev --no-hashes --format requirements-txt > requirements.txt
