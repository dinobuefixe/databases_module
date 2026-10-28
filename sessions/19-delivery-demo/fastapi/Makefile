# One command per step of the demonstration. Run `make help` for the list.
# `uv run` runs each command with the .venv that `make install` (uv sync) creates.
PORT ?= 8000
REPO_ROOT := ../../..

.PHONY: help install db setup run demo-concurrency demo-rebuild demo-explain demo

help:
	@echo "make install           uv sync (creates .venv from uv.lock) and .env from .env.example"
	@echo "make db                create s19_fastapi as a copy of Pagila (repository script)"
	@echo "make setup             account table, big_rental, Redis sets"
	@echo "make run               start the API on port $(PORT)"
	@echo "make demo-concurrency  50 concurrent withdrawals, naive vs atomic (API must be running)"
	@echo "make demo-rebuild      FLUSHDB, verify fails, rebuild, verify passes"
	@echo "make demo-explain      EXPLAIN (ANALYZE, BUFFERS) before and after the indexes"
	@echo "make demo              the three demos in order (API must be running)"

install:
	uv sync
	test -f .env || cp .env.example .env

db:
	$(REPO_ROOT)/scripts/create-db.sh s19_fastapi --pagila

setup: db
	uv run python -m scripts.setup

run:
	uv run uvicorn app.main:app --port $(PORT)

demo-concurrency:
	uv run python -m scripts.demo_concurrency

demo-rebuild:
	uv run python -m scripts.demo_rebuild

demo-explain:
	uv run python -m scripts.demo_explain

demo: demo-concurrency demo-rebuild demo-explain
