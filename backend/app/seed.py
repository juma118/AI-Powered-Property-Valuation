"""Database seed script.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.seed")

_SEED_CITIES: list[tuple[str, str]] = [
    ("Austin", "TX"),
    ("Denver", "CO"),
    ("Phoenix", "AZ"),
]

DEMO_EMAIL = "demo@proptech.io"
DEMO_PASSWORD = "demo1234"
DEMO_NAME = "Demo Agent"

# How many of the freshly ingested properties to push through AI analysis.
_ANALYSIS_COUNT = 8


async def _ensure_demo_user(db: AsyncSession) -> None:
    """Create the demo user if it does not already exist (idempotent)."""
    from app.models import User
    from app.security import hash_password

    existing = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if existing is not None:
        logger.info("seed: demo user already present (%s)", DEMO_EMAIL)
        return

    user = User(
        email=DEMO_EMAIL,
        hashed_password=hash_password(DEMO_PASSWORD),
        full_name=DEMO_NAME,
        role="agent",
    )
    db.add(user)
    await db.commit()
    logger.info("seed: created demo user %s / %s", DEMO_EMAIL, DEMO_PASSWORD)


async def _properties_empty(db: AsyncSession) -> bool:
    from app.models import Property

    count = await db.scalar(select(func.count()).select_from(Property))
    return int(count or 0) == 0


async def _ingest_markets(db: AsyncSession) -> list:
    """Ingest mock listings for each seed market. Returns ingested ORM rows."""
    from app.services import property_service

    ingested: list = []
    for city, state in _SEED_CITIES:
        try:
            rows = await property_service.ingest_search(
                db, city=city, state=state, limit=20
            )
            await db.commit()
            ingested.extend(rows or [])
            logger.info("seed: ingested %d listings for %s, %s", len(rows or []), city, state)
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            logger.exception("seed: ingest failed for %s, %s: %s", city, state, exc)
    return ingested


async def _embed(db: AsyncSession) -> None:
    from app.services import property_service

    try:
        embedded = await property_service.generate_embeddings(db, limit=500)
        await db.commit()
        logger.info("seed: embedded %s properties", int(embedded or 0))
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        logger.exception("seed: embedding stage failed: %s", exc)


async def _analyze(db: AsyncSession, ingested: list) -> None:
    from app.services import property_service

    targets = [getattr(p, "id", None) for p in ingested[:_ANALYSIS_COUNT]]
    targets = [t for t in targets if t is not None]
    analyzed = 0
    for pid in targets:
        try:
            await property_service.generate_analysis(db, pid)
            await db.commit()
            analyzed += 1
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            logger.exception("seed: analysis failed for %s: %s", pid, exc)
    logger.info("seed: generated %d analyses", analyzed)


async def seed(db: AsyncSession) -> dict:
    """Idempotently seed the database. Safe to run repeatedly.
    """
    report = {"properties_seeded": 0, "demo_user": DEMO_EMAIL}

    if await _properties_empty(db):
        logger.info("seed: properties table empty -> seeding mock data")
        ingested = await _ingest_markets(db)
        await _embed(db)
        await _analyze(db, ingested)
        report["properties_seeded"] = len(ingested)
    else:
        logger.info("seed: properties already present -> skipping listing seed")

    await _ensure_demo_user(db)
    return report


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    from app.database import AsyncSessionLocal, init_db

    await init_db()

    async with AsyncSessionLocal() as session:
        report = await seed(session)

    logger.info("seed: done -> %s", report)


if __name__ == "__main__":
    asyncio.run(_main())
