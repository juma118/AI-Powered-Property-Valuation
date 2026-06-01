from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.property import (
    ComparablesResponse,
    Property,
    PropertyAnalysis,
    SearchResponse,
)
from app.services import property_service

router = APIRouter(prefix="/properties", tags=["properties"])


class AnalysisRequest(BaseModel):
    property_id: UUID


@router.get("/search", response_model=SearchResponse)
async def search(
    db: AsyncSession = Depends(get_db),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    beds: int | None = Query(default=None, ge=0),
    baths: float | None = Query(default=None, ge=0),
    min_sqft: int | None = Query(default=None, ge=0),
    keywords: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    # Ensure the local store is populated for the requested area (mock-aware).
    await property_service.ingest_search(
        db,
        city=city,
        state=state,
        min_price=min_price,
        max_price=max_price,
        beds=beds,
        baths=baths,
        min_sqft=min_sqft,
        keywords=keywords,
    )

    results, total = await property_service.search_properties(
        db,
        city=city,
        state=state,
        min_price=min_price,
        max_price=max_price,
        beds=beds,
        baths=baths,
        min_sqft=min_sqft,
        keywords=keywords,
        limit=limit,
        offset=offset,
    )

    return SearchResponse(
        results=[Property.model_validate(p) for p in results],
        total=total,
    )


@router.get("/{property_id}", response_model=Property)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Property:
    prop = await property_service.get_property(db, property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )
    return Property.model_validate(prop)


@router.get("/{property_id}/comparables", response_model=ComparablesResponse)
async def comparables(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ComparablesResponse:
    prop = await property_service.get_property(db, property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    comps, stats = await property_service.get_comparables(db, property_id)
    return ComparablesResponse(
        comparables=[Property.model_validate(c) for c in comps],
        stats=stats,
    )


@router.get("/{property_id}/analysis", response_model=PropertyAnalysis)
async def get_analysis(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PropertyAnalysis:
    prop = await property_service.get_property(db, property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    analysis = getattr(prop, "analysis", None)
    if analysis is None:
        analysis = await property_service.generate_analysis(db, property_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not available for this property.",
        )
    return PropertyAnalysis.model_validate(analysis)


@router.post("/analysis", response_model=PropertyAnalysis, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    payload: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> PropertyAnalysis:
    prop = await property_service.get_property(db, payload.property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    analysis = await property_service.generate_analysis(db, payload.property_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate analysis for this property.",
        )
    return PropertyAnalysis.model_validate(analysis)
