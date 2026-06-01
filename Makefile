# ---------------------------------------------------------------------------
# AI-Powered Property Valuation & Lead Intelligence Platform
# Common developer tasks. Run `make up` then `make seed` for a full demo.
# ---------------------------------------------------------------------------

.PHONY: up down seed logs fe-dev be-dev

# Build images and start the whole stack (db, redis, backend, worker, frontend).
up:
	docker compose up --build

# Stop and remove containers (volumes are kept so data persists across restarts).
down:
	docker compose down

# Load deterministic mock properties / neighborhoods into the database.
# Run this AFTER the stack is up and healthy.
seed:
	docker compose exec backend python -m app.seed

# Tail logs from all services.
logs:
	docker compose logs -f

# Run the Next.js frontend locally (outside docker) against the dockerized API.
fe-dev:
	cd frontend && npm install && npm run dev

# Run the FastAPI backend locally (outside docker) with autoreload.
be-dev:
	cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
