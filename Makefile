.PHONY: help setup test gate lint fmt typecheck imports guards gate-proof \
        stack-up stack-down migrate serve front front-gate all-gates clean

PY := uv run
GUARDS := scripts/check_query_surface.py \
          scripts/check_access_consulted.py \
          scripts/check_no_create_all.py \
          scripts/check_prompts_versioned.py \
          scripts/check_contrast.py \
          scripts/check_logical_properties.py

# The guards import _guard.py as a sibling, so scripts/ must be importable.
GUARD_ENV := PYTHONPATH=scripts

help:
	@echo "make setup       Install backend and frontend dependencies"
	@echo "make stack-up    Start the stack (postgres, backend, frontend)"
	@echo "make test        Run the backend suite"
	@echo "make gate        Every architecture check (what CI runs)"
	@echo "make gate-proof  Prove each gate rejects a planted violation"
	@echo "make front-gate  Frontend checks (tsc, eslint, vitest) in the container"
	@echo "make all-gates   Both gates, backend then frontend"
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

gate: lint typecheck imports guards test
	@echo ""
	@echo "All gates passed, and each was proven to fail on a planted violation."

# The frontend's checks, kept out of `gate` on purpose. `gate` runs on the host through
# uv; there is no node here, so the frontend has to run inside its container, and folding
# it in would make the backend gate fail whenever Docker happens to be down. Two commands
# that each say what they need beats one that lies about it.
#
# Playwright is not included: it needs browser libraries the dev image does not carry.
# To run it locally once, inside the container:
#   pnpm exec playwright install --with-deps chromium && pnpm test:e2e
# Otherwise CI is where the browser tests live.
FRONT_CONTAINER ?= elenchus_frontend_1

front-gate:
	docker exec $(FRONT_CONTAINER) sh -c 'cd /app && \
		./node_modules/.bin/tsc --noEmit && \
		./node_modules/.bin/eslint . && \
		pnpm test'

# Both halves, for when you want the whole repo checked and have the stack up.
# Named `all-gates` rather than `gates`, which is one keystroke from `gate` and would
# quietly run the wrong thing on a typo.
all-gates: gate front-gate
	@echo ""
	@echo "Backend and frontend both clean."

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
