# AI-Powered Property Valuation & Lead Intelligence Platform

> A full-stack **proptech** application that turns raw listing data into actionable buying and investing intelligence — semantic search, AI valuations, neighborhood scoring, and a RAG chatbot, on a production-style microservice stack.

**Role:** Solo full-stack engineer (design → implementation → infra) · **Status:** Working MVP · **Type:** Portfolio / interview project

`Next.js 14` · `FastAPI` · `PostgreSQL + pgvector` · `Redis` · `Celery` · `OpenAI` · `Docker Compose`

---

## 🎯 Elevator Pitch (30 seconds)

> Home buyers and investors are drowning in listings but starved for *judgment* — a price and a bed count don't tell you if a home is fairly priced, a good investment, or in a strong neighborhood. I built a platform that answers those questions automatically: it ingests listing data, enriches it with neighborhood signals, generates an AI valuation with an investment score and pros/cons, computes comparable-sales stats, and lets a user **just ask in plain English** via retrieval-augmented chat over vector embeddings. The whole thing runs locally with one command and **zero external API keys**, because every external service has a deterministic mock fallback.

---

## The Problem

The raw fields on a listing (price, beds, sqft) don't answer the questions that actually drive a decision:

- Is this **priced fairly** versus comparable homes?
- What's the **investment upside** and **risk**?
- How good is the **neighborhood** — schools, walkability, commute, safety?
- Out of thousands of listings, **which fit me** — and can I just *ask*?

## The Solution

A platform that computes comparable-sales statistics, produces an AI valuation (pros/cons + investment/risk/buyer-fit scores), scores neighborhoods, recommends properties per user, and answers natural-language queries via RAG over a `pgvector` embedding index.

---

## 🏗️ Architecture at a Glance

```
 Next.js 14 (App Router, TS, Tailwind, React Query)
        │  HTTPS JSON · Bearer JWT
        ▼
 FastAPI (/api)  ──  auth · properties · dashboard · chat · saved
   services/  valuation · comparables · analysis · search · RAG chat
   external clients (RentCast · Google Maps · OpenAI)  ← mock fallback
        │ async SQLAlchemy            │ Celery tasks
        ▼                             ▼
 Postgres 16 + pgvector  ◀────▶  Celery worker  ──▶  Redis 7 (broker/backend)
 (users, properties,            ingest → enrich
  neighborhoods, analyses,      → embed pipeline
  embedding Vector(1536))
```

**Example request flow (semantic chat):** browser → `POST /api/chat/query` → embed the query (OpenAI, or a deterministic hash vector in mock mode) → `pgvector` cosine search over `properties.embedding` → build context → OpenAI chat → return `{ answer, properties, sources }`.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, TanStack React Query, axios, Leaflet/OpenStreetMap |
| **Backend** | FastAPI, Python 3.11, async SQLAlchemy 2.x (asyncpg), Pydantic v2 + pydantic-settings |
| **Auth** | JWT (HS256, python-jose), bcrypt password hashing (passlib) |
| **AI / Vectors** | OpenAI `text-embedding-3-small` (1536-d) + `gpt-4o-mini`, pgvector cosine search |
| **Data / Infra** | PostgreSQL 16 + pgvector, Redis 7, Celery, httpx, Docker Compose |

---

## ✨ Key Features

- **Semantic RAG Chat** — ask in natural language; answers are grounded in the actual inventory via vector retrieval, and the source properties are returned alongside the answer.
- **AI Valuation & Analysis** — per-property summary, pros/cons, investment score (0–100), risk score, buyer-fit score, price evaluation, and estimated value, persisted to the database.
- **Comparable Sales** — nearest comps plus stats (avg price, avg price/sqft, subject price/sqft) for fair-value context.
- **Neighborhood Intelligence** — school, walk, crime scores, commute time, restaurant count, and nearby schools per property.
- **Filterable Search + Interactive Map** — city/state/price/beds/baths/sqft/keyword filtering, with a Leaflet + OpenStreetMap map view (price-pin markers, click-through popups) that needs **no map API key**.
- **Personalized Dashboard & Recommendations** — KPIs, recent activity, and per-user property recommendations.
- **Auth & Saved Properties** — JWT register/login/refresh/me and saved listings with notes and labels.

---

## 🔧 Engineering Highlights (interview talking points)

**1. Retrieval-Augmented Generation over pgvector.**
Each property is reduced to a descriptive text blob (address, type, beds, sqft, description, neighborhood signals), embedded to a 1536-d vector, and stored in a `Vector(1536)` column. Chat queries are embedded and matched by cosine similarity directly in Postgres — no separate vector DB to operate. *Talks to: RAG design, embeddings, vector search, keeping infra lean.*

**2. "Runs with zero external accounts" — a deterministic mock layer.**
Every external dependency (RentCast, Google Maps, OpenAI embeddings, OpenAI chat) has a mock fallback that activates when its key is empty or `USE_MOCK_DATA=true`. Embeddings fall back to a **hash-derived pseudo-vector**, so vector search behaves identically offline and across runs. *Talks to: dependency isolation, testability, reproducibility, graceful degradation, good DX.*

**3. Async, non-blocking data pipeline.**
Ingestion and enrichment run as **Celery tasks** (Redis broker/backend) so heavy I/O never blocks API requests: ingest → enrich neighborhood → embed → (on-demand) analyze. The API stays responsive while the worker does the slow work. *Talks to: background jobs, queue architecture, separation of concerns.*

**4. Type-safe contract end to end.**
Pydantic v2 schemas on the backend mirror hand-written TypeScript interfaces on the frontend, with React Query managing server state, caching, and request lifecycle. *Talks to: API design, type safety, frontend data fetching.*

**5. Containerized, one-command stack.**
`docker compose` brings up db, redis, backend, worker, and frontend; schema is created on startup and the DB auto-seeds ~30 listings, AI analyses, and a demo user — so a reviewer goes from clone to working app in minutes. *Talks to: infra, DX, onboarding.*

---

## 🐛 A Real Debugging Story (great for "tell me about a bug")

A reviewer hit a **CORS error** logging in. The surface fix (add the frontend origin) didn't work — so I traced the config precedence: the running backend was a **Docker container** whose Compose `environment:` block *hardcoded* `CORS_ORIGINS`, which **overrides** the `.env` file. Separately, the frontend they were viewing was a **production image built before the change**, so it served stale code regardless of refresh. The lesson I talk about: *when a fix "doesn't work," verify what's actually running vs. what you edited* — config precedence (inline env > env_file) and build-time vs. run-time artifacts. I fixed it at every layer (`.env`, `config.py` default, and the Compose override) and documented the rebuild step.

---

## 📊 Scope & Numbers

- **6 feature areas** (search, valuation, comparables, neighborhood, dashboard/recs, RAG chat) + auth + saved.
- **~15 REST endpoints** under a versioned `/api` prefix, fully documented via FastAPI's auto-generated Swagger.
- **5 services** orchestrated in Docker Compose (Postgres+pgvector, Redis, FastAPI API, Celery worker, Next.js).
- **6 frontend routes** (login, dashboard, search, property detail, chat, saved).
- **1536-d** embeddings, cosine similarity search in-database.

---

## 🚀 What I'd Build Next

- **Alembic migrations** (the MVP creates schema via `create_all`; a real deployment needs versioned migrations).
- **Automated tests + CI** — pytest for services/RAG, Playwright for the critical UI flows, GitHub Actions on PR.
- **Streaming chat responses** and conversation memory.
- **Real provider keys in staging** to validate the live RentCast/Google/OpenAI paths end to end.
- **Observability** — structured logging, request tracing, and a metrics dashboard for the worker pipeline.

---

## ▶️ Try It

```bash
cp .env.example .env      # mock mode on by default — no keys needed
docker compose up --build -d
# open http://localhost:3000   ·   API docs: http://localhost:8000/docs
# demo login: demo@proptech.io / demo1234
```

*See [README.md](README.md) for full setup, API reference, and the data-pipeline deep dive.*
