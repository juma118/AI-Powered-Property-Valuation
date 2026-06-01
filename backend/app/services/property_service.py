"""Property business logic used by the routers.

Coordinates the RentCast client, enrichment service, and AI service with the
database. All DB operations are async (SQLAlchemy 2.x async session).

Conventions:
- `params` may be a dict or any object exposing the search attributes
  (city, state, min_price, max_price, beds, baths, min_sqft, keywords,
  limit, offset).
- `id` values are property UUIDs (str or uuid.UUID).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Analysis, Neighborhood, Property
from app.services.ai_service import AIService
from app.services.enrichment_service import EnrichmentService
from app.services.rentcast_client import RentCastClient

# Property columns we are allowed to set from a normalized listing dict.
_PROPERTY_FIELDS = (
    "external_id",
    "address",
    "city",
    "state",
    "zip",
    "price",
    "beds",
    "bathrooms",
    "sqft",
    "lot_size",
    "year_built",
    "property_type",
    "lat",
    "lng",
    "description",
    "photos",
    "status",
    "listed_date",
)

# Threshold below which a DB search triggers a live ingest.
_MIN_RESULTS_BEFORE_INGEST = 3


# ---------------------------------------------------------------------------
# params helpers
# ---------------------------------------------------------------------------
_SEARCH_PARAM_NAMES = (
    "city",
    "state",
    "min_price",
    "max_price",
    "beds",
    "baths",
    "min_sqft",
    "keywords",
    "limit",
    "offset",
)


def _p(params: Any, name: str, default: Any = None) -> Any:
    if params is None:
        return default
    if isinstance(params, dict):
        return params.get(name, default)
    return getattr(params, name, default)


def _merge_params(params: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Accept either a params dict/object (positional) or keyword arguments.

    All public service entry points accept keyword args (the convention used by
    the routers, seed, pipeline and workers); a positional dict/object is also
    supported for flexibility.
    """
    merged: dict[str, Any] = {}
    if isinstance(params, dict):
        merged.update(params)
    elif params is not None:
        for name in _SEARCH_PARAM_NAMES:
            value = getattr(params, name, None)
            if value is not None:
                merged[name] = value
    for key, value in kwargs.items():
        if value is not None:
            merged[key] = value
    return merged


def _parse_listed_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _as_uuid(value: Any) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------
async def ingest_search(db: AsyncSession, params: Any = None, **kwargs: Any) -> list[Property]:
    """Fetch listings from RentCast, upsert, enrich, embed, and return rows."""
    params = _merge_params(params, kwargs)
    client = RentCastClient()
    enrichment = EnrichmentService()
    ai = AIService()

    limit = int(_p(params, "limit", 20) or 20)

    listings = await client.search_listings(
        city=_p(params, "city"),
        state=_p(params, "state"),
        min_price=_p(params, "min_price"),
        max_price=_p(params, "max_price"),
        beds=_p(params, "beds"),
        baths=_p(params, "baths"),
        min_sqft=_p(params, "min_sqft"),
        limit=limit,
    )

    ingested: list[Property] = []
    for listing in listings:
        external_id = listing.get("external_id")
        if not external_id:
            continue

        existing = await db.scalar(
            select(Property).where(Property.external_id == external_id)
        )

        if existing is None:
            prop = Property()
            _apply_listing(prop, listing)
            db.add(prop)
            await db.flush()  # assign PK
            is_new = True
        else:
            _apply_listing(existing, listing)
            prop = existing
            is_new = False

        # Compute embedding from description (only when missing or new).
        if is_new or getattr(prop, "embedding", None) is None:
            text = _embedding_text(prop)
            try:
                prop.embedding = await ai.embed(text)
            except Exception:
                prop.embedding = None

        # Enrich neighborhood (create if absent).
        await _ensure_neighborhood(db, prop, enrichment)

        ingested.append(prop)

    await db.commit()
    for prop in ingested:
        await db.refresh(prop)
    return ingested


def _apply_listing(prop: Property, listing: dict[str, Any]) -> None:
    for field in _PROPERTY_FIELDS:
        if field not in listing:
            continue
        value = listing[field]
        if field == "listed_date":
            value = _parse_listed_date(value)
        setattr(prop, field, value)


def _embedding_text(prop: Property) -> str:
    parts = [
        getattr(prop, "description", "") or "",
        f"{getattr(prop, 'beds', '')} bed",
        f"{getattr(prop, 'bathrooms', '')} bath",
        f"{getattr(prop, 'sqft', '')} sqft",
        getattr(prop, "property_type", "") or "",
        getattr(prop, "city", "") or "",
        getattr(prop, "state", "") or "",
    ]
    return " ".join(str(p) for p in parts if p).strip()


async def _ensure_neighborhood(
    db: AsyncSession, prop: Property, enrichment: EnrichmentService
) -> Neighborhood:
    existing = await db.scalar(
        select(Neighborhood).where(Neighborhood.property_id == prop.id)
    )
    if existing is not None:
        return existing

    data = await enrichment.build_neighborhood(prop)
    neighborhood = Neighborhood(property_id=prop.id, **data)
    db.add(neighborhood)
    await db.flush()
    return neighborhood


# ---------------------------------------------------------------------------
# Embeddings backfill
# ---------------------------------------------------------------------------
async def generate_embeddings(db: AsyncSession, limit: int = 500) -> int:
    """Compute and store embeddings for properties currently missing one.

    Returns the number of properties embedded. Used by the seed script and the
    nightly pipeline (the "Generate Embeddings" stage).
    """
    ai = AIService()
    stmt = (
        select(Property)
        .where(Property.embedding.is_(None))
        .limit(limit)
    )
    rows = list((await db.scalars(stmt)).all())

    embedded = 0
    for prop in rows:
        try:
            prop.embedding = await ai.embed(_embedding_text(prop))
            embedded += 1
        except Exception:
            prop.embedding = None
    if embedded:
        await db.commit()
    return embedded


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
async def search_properties(
    db: AsyncSession, params: Any = None, **kwargs: Any
) -> tuple[list[Property], int]:
    """Query the DB with filters; ingest live data if too few results."""
    params = _merge_params(params, kwargs)
    rows, total = await _query_properties(db, params)

    if total < _MIN_RESULTS_BEFORE_INGEST:
        await ingest_search(db, params)
        rows, total = await _query_properties(db, params)

    return rows, total


def _build_filters(params: Any) -> list[Any]:
    filters: list[Any] = []
    city = _p(params, "city")
    state = _p(params, "state")
    min_price = _p(params, "min_price")
    max_price = _p(params, "max_price")
    beds = _p(params, "beds")
    baths = _p(params, "baths")
    min_sqft = _p(params, "min_sqft")
    keywords = _p(params, "keywords")

    if city:
        filters.append(func.lower(Property.city) == str(city).strip().lower())
    if state:
        filters.append(func.lower(Property.state) == str(state).strip().lower())
    if min_price is not None:
        filters.append(Property.price >= min_price)
    if max_price is not None:
        filters.append(Property.price <= max_price)
    if beds is not None:
        filters.append(Property.beds >= beds)
    if baths is not None:
        filters.append(Property.bathrooms >= baths)
    if min_sqft is not None:
        filters.append(Property.sqft >= min_sqft)
    if keywords:
        like = f"%{str(keywords).strip()}%"
        filters.append(
            or_(
                Property.description.ilike(like),
                Property.address.ilike(like),
                Property.city.ilike(like),
                Property.property_type.ilike(like),
            )
        )
    return filters


async def _query_properties(db: AsyncSession, params: Any) -> tuple[list[Property], int]:
    filters = _build_filters(params)
    limit = int(_p(params, "limit", 20) or 20)
    offset = int(_p(params, "offset", 0) or 0)

    count_stmt = select(func.count()).select_from(Property)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int(await db.scalar(count_stmt) or 0)

    stmt = select(Property)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Property.created_at.desc()).limit(limit).offset(offset)

    result = await db.scalars(stmt)
    rows = list(result.all())
    return rows, total


# ---------------------------------------------------------------------------
# Single property + comparables + analysis
# ---------------------------------------------------------------------------
async def get_property(db: AsyncSession, id: Any) -> Optional[Property]:
    """Return a Property by id (None if not found)."""
    try:
        pid = _as_uuid(id)
    except (ValueError, AttributeError, TypeError):
        return None
    return await db.get(Property, pid)


async def get_comparables(db: AsyncSession, id: Any) -> tuple[list[Property], dict[str, Any]]:
    """Return ``(comparables, stats)``.

    Comparables: same city, sqft within +/- 30% of subject, excluding self,
    limited to 6, ordered by closeness in sqft.
    """
    subject = await get_property(db, id)
    if subject is None:
        return [], {
            "avg_price": 0.0,
            "avg_price_per_sqft": 0.0,
            "count": 0,
            "subject_price_per_sqft": 0.0,
        }

    subject_sqft = subject.sqft or 0
    low_sqft = int(subject_sqft * 0.7) if subject_sqft else 0
    high_sqft = int(subject_sqft * 1.3) if subject_sqft else 0

    stmt = select(Property).where(Property.id != subject.id)
    if subject.city:
        stmt = stmt.where(func.lower(Property.city) == subject.city.lower())
    if subject_sqft:
        stmt = stmt.where(Property.sqft >= low_sqft, Property.sqft <= high_sqft)
        stmt = stmt.order_by(func.abs(Property.sqft - subject_sqft))
    else:
        stmt = stmt.order_by(Property.created_at.desc())
    stmt = stmt.limit(6)

    comps = list((await db.scalars(stmt)).all())

    prices = [float(c.price) for c in comps if c.price is not None]
    ppsf_values = [
        float(c.price) / c.sqft for c in comps if c.price is not None and c.sqft
    ]

    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
    avg_ppsf = round(sum(ppsf_values) / len(ppsf_values), 2) if ppsf_values else 0.0
    subject_ppsf = (
        round(float(subject.price) / subject.sqft, 2)
        if subject.price is not None and subject.sqft
        else 0.0
    )

    return comps, {
        "avg_price": avg_price,
        "avg_price_per_sqft": avg_ppsf,
        "count": len(comps),
        "subject_price_per_sqft": subject_ppsf,
    }


async def get_analysis(db: AsyncSession, id: Any) -> Optional[Analysis]:
    """Return the persisted Analysis for a property, if any."""
    try:
        pid = _as_uuid(id)
    except (ValueError, AttributeError, TypeError):
        return None
    return await db.scalar(select(Analysis).where(Analysis.property_id == pid))


async def generate_analysis(db: AsyncSession, id: Any) -> Optional[Analysis]:
    """Build neighborhood + comparables, run AI analysis, upsert Analysis row."""
    subject = await get_property(db, id)
    if subject is None:
        return None

    enrichment = EnrichmentService()
    ai = AIService()

    # Ensure neighborhood exists for richer analysis context.
    neighborhood = await _ensure_neighborhood(db, subject, enrichment)

    comparables, _stats = await get_comparables(db, subject.id)

    analysis_data = await ai.analyze_property(subject, neighborhood, comparables)

    existing = await db.scalar(
        select(Analysis).where(Analysis.property_id == subject.id)
    )
    if existing is None:
        analysis = Analysis(property_id=subject.id, **analysis_data)
        db.add(analysis)
    else:
        for key, value in analysis_data.items():
            setattr(existing, key, value)
        analysis = existing

    await db.commit()
    await db.refresh(analysis)
    return analysis


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------
async def semantic_search(db: AsyncSession, query: str, limit: int = 6) -> list[Property]:
    """Embed the query and order by pgvector cosine distance.

    Falls back to ILIKE keyword search when no embeddings are available or the
    vector query fails.
    """
    query = (query or "").strip()
    if not query:
        return []

    ai = AIService()

    # Only attempt vector search if at least one property has an embedding.
    has_embeddings = await db.scalar(
        select(func.count()).select_from(Property).where(Property.embedding.isnot(None))
    )

    if has_embeddings:
        try:
            query_vec = await ai.embed(query)
            # pgvector cosine distance operator <=> exposed via .cosine_distance
            distance = Property.embedding.cosine_distance(query_vec)
            stmt = (
                select(Property)
                .where(Property.embedding.isnot(None))
                .order_by(distance)
                .limit(limit)
            )
            rows = list((await db.scalars(stmt)).all())
            if rows:
                return rows
        except Exception:
            # Fall through to keyword search.
            pass

    # Keyword fallback.
    like = f"%{query}%"
    stmt = (
        select(Property)
        .where(
            or_(
                Property.description.ilike(like),
                Property.address.ilike(like),
                Property.city.ilike(like),
                Property.property_type.ilike(like),
            )
        )
        .order_by(Property.created_at.desc())
        .limit(limit)
    )
    return list((await db.scalars(stmt)).all())
