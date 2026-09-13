.PHONY: help setup test gate lint fmt typecheck imports guards gate-proof eval \
        stack-up stack-down migrate serve front front-gate all-gates clean \
        interp interp-gate

PY := uv run
GUARDS := scripts/check_query_surface.py \
          scripts/check_access_consulted.py \
          scripts/check_no_create_all.py \
          scripts/check_prompts_versioned.py \
          scripts/check_contrast.py \
          scripts/check_logical_properties.py \
          scripts/eval_report.py

# The guards import _guard.py as a sibling, so scripts/ must be importable.
GUARD_ENV := PYTHONPATH=scripts

help:
	@echo "make setup       Install backend and frontend dependencies"
	@echo "make stack-up    Start the stack (postgres, backend, frontend)"
	@echo "make test        Run the backend suite"
	@echo "make gate        Every architecture check (what CI runs)"
	@echo "make gate-proof  Prove each gate rejects a planted violation"
	@echo "make eval        The replay corpus in numbers, and what must not regress"
	@echo "make front-gate  Frontend checks (tsc, eslint, vitest) in the container"
	@echo "make all-gates   Both gates, backend then frontend"
	@echo "make interp      Start the interpretability model on the host (Qwen3-0.6B)"
	@echo "make interp-gate The interpretability service's checks"
	@echo "make serve       Run the backend on the host, against the compose Postgres"

setup:
	cd backend && uv sync
	cd frontend && pnpm install

stack-up:
	docker compose up -d
	@echo "backend http://localhost:8000  frontend http://localhost:3000"

stack-down:
	docker compose stop

migrate:
	cd backend && $(PY) alembic upgrade head

serve:
	cd backend && $(PY) uvicorn app.main:app --reload --port 8000

front:
	cd frontend && pnpm dev

test:
	./scripts/test.sh

lint:
	cd backend && $(PY) ruff check app tests scripts
	cd backend && $(PY) black --check app tests scripts

fmt:
	cd backend && $(PY) black app tests scripts

typecheck:
	cd backend && $(PY) mypy app

imports:
	cd backend && $(PY) lint-imports

guards:
	@cd backend && for guard in $(GUARDS); do \
		echo "--> $$guard"; \
		$(GUARD_ENV) $(PY) python $$guard || exit 1; \
	done

# gate-proof is what makes the rest of this file trustworthy: it plants a
# deliberate violation for each guard and asserts a non-zero exit. A gate that
# has never been observed to reject anything is decoration.
gate-proof:
	./scripts/test.sh tests/test_gates.py -v

# The corpus in numbers. Runs inside `gate` too, where it ratchets; run alone it is the
# scorecard you read before and after changing the model. Nothing here needs a key or a
# database: it reads the committed fixtures.
eval:
	@cd backend && $(GUARD_ENV) $(PY) python scripts/eval_report.py

gate: lint typecheck imports guards test
	@echo ""
	@echo "All gates passed, and each was proven to fail on a planted violation."

# The frontend's checks, kept out of `gate` on purpose. `gate` runs on the host through
# uv; there is no node here, so the frontend has to run inside its container, and folding
# it in would make the backend gate fail whenever Docker happens to be down. Two commands
# that each say what they need beats one that lies about it.
FRONT_CONTAINER ?= elenchus_frontend_1

front-gate:
	docker exec $(FRONT_CONTAINER) sh -c 'cd /app && \
		./node_modules/.bin/tsc --noEmit && \
		./node_modules/.bin/eslint . && \
		pnpm test'

# Both halves, for when you want the whole repo checked and have the stack up.
# Named `all-gates` rather than `gates`, which is one keystroke from `gate` and would
# quietly run the wrong thing on a typo.
# The interpretability service (interp/): Qwen3-0.6B on the host, for the lens pages.
# On the host rather than in the stack so a Mac reads with its GPU. It listens on every
# interface because the backend container reaches it through host.docker.internal, so it
# takes INTERP_TOKEN, and only that, from .env: the token is the lock, and the process has
# no use for any other secret. The first run downloads about 1.5 GB of weights.
interp:
	cd interp && INTERP_HOST=0.0.0.0 \
		INTERP_TOKEN="$$(grep -E '^INTERP_TOKEN=' ../.env | cut -d= -f2-)" \
		uv run python -m elenchus_interp

# Its own gate, because it is its own project: PyTorch never enters the backend's
# environment, and the backend gate stays runnable without it.
interp-gate:
	cd interp && uv run ruff check . && uv run black --check elenchus_interp tests && \
		uv run mypy elenchus_interp && uv run pytest -q

all-gates: gate front-gate
	@echo ""
	@echo "Backend and frontend both clean."

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
