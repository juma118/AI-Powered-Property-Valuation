"""Celery tasks implementing the proptech data pipeline.

Pipeline stages (per stage of the ETL):

    Pull -> Normalize -> Store -> Geocode -> Embed -> Analyze

Each task is fully self-contained: it opens its **own** async SQLAlchemy
session (Celery workers run in synchronous worker processes, so we bridge to
async via ``asyncio.run``) and delegates to the relevant service in
``app.services``. Tasks are defensive: every task body is wrapped in
try/except with structured logging so a single failure never poisons the
worker, and a serializable result dict is always returned.

Service contract assumed (see ``app.services.property_service``):

    async def ingest_search(db, *, city, state, limit=...) -> list[Property]
    async def generate_embeddings(db, *, limit=...) -> int
    async def generate_analysis(db, property_id) -> Analysis

Run a worker::

    celery -A app.workers.celery_app:celery_app worker --loglevel=info
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Iterable, Optional
from uuid import UUID

from app.database import AsyncSessionLocal
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.tasks")

# ---------------------------------------------------------------------------
# Async bridge helpers
# ---------------------------------------------------------------------------


def _run(coro) -> Any:
    """Run an async coroutine to completion from a sync Celery worker.

    Uses a fresh event loop each call so it is safe regardless of whether the
    worker pool has a pre-existing loop bound to the thread.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            loop.close()


async def _with_session(fn):
    """Open a dedicated async session, run ``fn(session)``, commit/rollback."""
    async with AsyncSessionLocal() as session:
        try:
            result = await fn(session)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@celery_app.task(name="app.workers.tasks.refresh_listings", bind=True, max_retries=3)
def refresh_listings(self, city: str, state: str, limit: int = 20) -> dict[str, Any]:
    """Pull -> Normalize -> Store -> Geocode for a single market.

    Delegates to ``property_service.ingest_search`` which performs the RentCast
    pull, normalization, upsert into ``properties``, and neighborhood/geocode
    enrichment. Returns a summary dict suitable for the Celery result backend.
    """
    from app.services import property_service

    async def _job(session):
        listings = await property_service.ingest_search(
            session, city=city, state=state, limit=limit
        )
        return [str(getattr(p, "id", p)) for p in (listings or [])]

    try:
        ids = _run(_with_session(_job))
        logger.info(
            "refresh_listings: ingested %d listings for %s, %s",
            len(ids),
            city,
            state,
        )
        return {"ok": True, "city": city, "state": state, "ingested": len(ids), "ids": ids}
    except Exception as exc:  # noqa: BLE001
        logger.exception("refresh_listings failed for %s, %s: %s", city, state, exc)
        try:
            raise self.retry(exc=exc, countdown=30)
        except self.MaxRetriesExceededError:
            return {"ok": False, "city": city, "state": state, "error": str(exc)}


@celery_app.task(name="app.workers.tasks.generate_embeddings_task", bind=True, max_retries=2)
def generate_embeddings_task(self, limit: int = 100) -> dict[str, Any]:
    """Embed stage: generate vector embeddings for properties missing one.

    Delegates to ``property_service.generate_embeddings`` which selects rows
    where ``embedding IS NULL`` and populates them (OpenAI or deterministic
    hash-based fallback). Returns the number embedded.
    """
    from app.services import property_service

    async def _job(session):
        return await property_service.generate_embeddings(session, limit=limit)

    try:
        count = _run(_with_session(_job))
        embedded = int(count or 0)
        logger.info("generate_embeddings_task: embedded %d properties", embedded)
        return {"ok": True, "embedded": embedded}
    except Exception as exc:  # noqa: BLE001
        logger.exception("generate_embeddings_task failed: %s", exc)
        try:
            raise self.retry(exc=exc, countdown=30)
        except self.MaxRetriesExceededError:
            return {"ok": False, "error": str(exc)}


@celery_app.task(name="app.workers.tasks.run_ai_analysis", bind=True, max_retries=3)
def run_ai_analysis(self, property_id: str) -> dict[str, Any]:
    """Analyze stage: generate + persist the AI analysis for one property.

    Delegates to ``property_service.generate_analysis``. ``property_id`` is
    passed as a string (Celery JSON serialization) and coerced to ``UUID``.
    """
    from app.services import property_service

    try:
        pid: Any = UUID(str(property_id))
    except (ValueError, AttributeError, TypeError):
        pid = property_id

    async def _job(session):
        return await property_service.generate_analysis(session, pid)

    try:
        analysis = _run(_with_session(_job))
        analysis_id = str(getattr(analysis, "id", "")) if analysis is not None else None
        logger.info("run_ai_analysis: analyzed property %s", property_id)
        return {"ok": True, "property_id": str(property_id), "analysis_id": analysis_id}
    except Exception as exc:  # noqa: BLE001
        logger.exception("run_ai_analysis failed for %s: %s", property_id, exc)
        try:
            raise self.retry(exc=exc, countdown=30)
        except self.MaxRetriesExceededError:
            return {"ok": False, "property_id": str(property_id), "error": str(exc)}


@celery_app.task(name="app.workers.tasks.warm_cache")
def warm_cache() -> dict[str, Any]:
    """Warm read-side caches (dashboard recents, popular searches).

    For the MVP this simply runs the lightweight dashboard/recents queries so
    connection pools and (future) Redis caches are primed. It is robust to the
    optional ``property_service`` cache hooks not existing yet.
    """
    from app.services import property_service

    async def _job(session):
        warmed = 0
        # Prefer an explicit cache-warming hook if the service defines one.
        warm_fn = getattr(property_service, "warm_cache", None)
        if callable(warm_fn):
            result = await warm_fn(session)
            return int(result or 0)
        # Fallback: touch the recent-properties path to prime the pool/cache.
        recent_fn = getattr(property_service, "list_recent", None)
        if callable(recent_fn):
            rows = await recent_fn(session, limit=20)
            warmed = len(rows or [])
        return warmed

    try:
        warmed = _run(_with_session(_job))
        logger.info("warm_cache: warmed %s entries", warmed)
        return {"ok": True, "warmed": int(warmed or 0)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("warm_cache failed: %s", exc)
        return {"ok": False, "error": str(exc)}


@celery_app.task(name="app.workers.tasks.run_pipeline_task")
def run_pipeline_task(cities: Optional[Iterable[Any]] = None) -> dict[str, Any]:
    """Scheduled orchestrator: run the full ETL pipeline for a set of markets.

    ``cities`` is a list of ``[city, state]`` pairs (JSON-friendly). Invoked by
    Celery beat (see ``celery_app.beat_schedule``). Delegates to
    ``pipeline.run_full_pipeline`` which performs ingest + embed + analyze.
    """
    from app.workers.pipeline import run_full_pipeline

    normalized: list[tuple[str, str]] = []
    for entry in cities or []:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            normalized.append((str(entry[0]), str(entry[1])))

    if not normalized:
        normalized = [("Austin", "TX"), ("Denver", "CO"), ("Phoenix", "AZ")]

    async def _job(session):
        return await run_full_pipeline(session, normalized)

    try:
        report = _run(_with_session(_job))
        logger.info("run_pipeline_task: completed for %d markets", len(normalized))
        return {"ok": True, "report": report}
    except Exception as exc:  # noqa: BLE001
        logger.exception("run_pipeline_task failed: %s", exc)
        return {"ok": False, "error": str(exc)}


__all__ = [
    "refresh_listings",
    "generate_embeddings_task",
    "run_ai_analysis",
    "warm_cache",
    "run_pipeline_task",
]
