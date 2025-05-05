PROJECT_NAME := $(notdir $(shell pwd))
CONTAINER_NAME := $(PROJECT_NAME)-app-1

all: down build up_d

build:
	docker compose build

up:
	docker compose up

up_d:
	docker compose up -d

down:
	docker compose down

logs:
	docker logs $(CONTAINER_NAME) -f --tail 500

fmt:
	uv run ruff check --select I --fix .
	uv run ruff format

lint:
	uv run ruff check

checks: fmt lint

requirements:
	uv export --no-group dev --no-hashes --format requirements-txt > requirements.txt
