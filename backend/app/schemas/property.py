from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PropertyNeighborhood(BaseModel):
    """Neighborhood intelligence for a property (ORM-serializable)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    school_score: float | None = None
    restaurants_count: int | None = None
    commute_time: int | None = None
    walk_score: int | None = None
    crime_score: float | None = None
    nearby_schools: list[dict] | None = None
    created_at: datetime


class PropertyAnalysis(BaseModel):
    """AI-generated valuation / investment analysis (ORM-serializable)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    summary: str | None = None
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    investment_score: int | None = None
    risk_score: str | None = None
    buyer_score: int | None = None
    price_evaluation: str | None = None
    estimated_value: Decimal | None = None
    created_at: datetime


class Property(BaseModel):
    """Full property representation.

    Mirrors the ``properties`` table exactly. The raw ``embedding`` column is
    intentionally excluded from output. Optional ``neighborhood`` and
    ``analysis`` are embedded when present on the ORM object.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str | None = None
    address: str
    city: str
    state: str
    zip: str
    price: Decimal | None = None
    beds: int | None = None
    bathrooms: float | None = None
    sqft: int | None = None
    lot_size: int | None = None
    year_built: int | None = None
    property_type: str | None = None
    lat: float | None = None
    lng: float | None = None
    description: str | None = None
    photos: list[str] = Field(default_factory=list)
    status: str = "active"
    listed_date: date | None = None
    created_at: datetime
    updated_at: datetime

    neighborhood: PropertyNeighborhood | None = None
    analysis: PropertyAnalysis | None = None


class SearchResponse(BaseModel):
    results: list[Property] = Field(default_factory=list)
    total: int = 0


class ComparablesStats(BaseModel):
    avg_price: float | None = None
    avg_price_per_sqft: float | None = None
    count: int = 0
    subject_price_per_sqft: float | None = None


class ComparablesResponse(BaseModel):
    comparables: list[Property] = Field(default_factory=list)
    stats: ComparablesStats = Field(default_factory=ComparablesStats)
