"""The scheduled ETL pipeline.

``run_full_pipeline`` is the orchestrated, end-to-end data flow that the
nightly Celery beat job (``app.workers.tasks.run_pipeline_task``) executes. It
can also be invoked directly in tests or from a one-off script.

Pipeline stages, end to end:

    Pull -> Normalize -> Store -> Geocode   (property_service.ingest_search)
    Embed                                    (property_service.generate_embeddings)
    Analyze                                  (property_service.generate_analysis)

The function is intentionally defensive: a failure ingesting or analyzing one
market never aborts the others. It returns a structured report dict so the
caller (and the Celery result backend) gets a clear picture of what happened.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.workers.pipeline")

# How many freshly ingested properties to push through AI analysis per market.
_ANALYSIS_LIMIT_PER_MARKET = 8


async def run_full_pipeline(
    db: AsyncSession,
    cities: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    """Run ingest + embed + analyze for a set of ``(city, state)`` markets.

    Parameters
    ----------
    db:
        An open async session. The caller owns its lifecycle (commit/close);
        this function flushes/commits incrementally so partial progress is
        durable even if a later stage fails.
    cities:
        Iterable of ``(city, state)`` tuples to refresh.

    Returns
    -------
    dict
        ``{"markets": [...], "ingested": int, "embedded": int, "analyzed": int}``
    """
    from app.services import property_service

    report: dict[str, Any] = {
        "markets": [],
        "ingested": 0,
        "embedded": 0,
        "analyzed": 0,
        "errors": [],
    }

    # ------------------------------------------------------------------
    # Stage 1-4: Pull -> Normalize -> Store -> Geocode, per market.
    # ------------------------------------------------------------------
    ingested_ids: list[Any] = []
    for city, state in cities:
        market = {"city": city, "state": state, "ingested": 0}
        try:
            listings = await property_service.ingest_search(
                db, city=city, state=state, limit=20
            )
            await db.commit()
            ids = [getattr(p, "id", None) for p in (listings or [])]
            ids = [i for i in ids if i is not None]
            ingested_ids.extend(ids)
            market["ingested"] = len(ids)
            report["ingested"] += len(ids)
            logger.info("pipeline: ingested %d for %s, %s", len(ids), city, state)
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            logger.exception("pipeline ingest failed for %s, %s: %s", city, state, exc)
            report["errors"].append(
                {"stage": "ingest", "city": city, "state": state, "error": str(exc)}
            )
        report["markets"].append(market)

    # ------------------------------------------------------------------
    # Stage 5: Embed (all properties currently missing an embedding).
    # ------------------------------------------------------------------
    try:
        embedded = await property_service.generate_embeddings(db, limit=500)
        await db.commit()
        report["embedded"] = int(embedded or 0)
        logger.info("pipeline: embedded %d properties", report["embedded"])
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        logger.exception("pipeline embed stage failed: %s", exc)
        report["errors"].append({"stage": "embed", "error": str(exc)})

    # ------------------------------------------------------------------
    # Stage 6: Analyze a capped number of newly ingested properties per run
    # to keep the nightly job bounded (and avoid re-analyzing everything).
    # ------------------------------------------------------------------
    to_analyze = ingested_ids[: _ANALYSIS_LIMIT_PER_MARKET * max(1, len(cities))]
    for pid in to_analyze:
        try:
            await property_service.generate_analysis(db, pid)
            await db.commit()
            report["analyzed"] += 1
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            logger.exception("pipeline analyze failed for %s: %s", pid, exc)
            report["errors"].append(
                {"stage": "analyze", "property_id": str(pid), "error": str(exc)}
            )

    logger.info(
        "pipeline complete: ingested=%d embedded=%d analyzed=%d errors=%d",
        report["ingested"],
        report["embedded"],
        report["analyzed"],
        len(report["errors"]),
    )
    return report


__all__ = ["run_full_pipeline"]
