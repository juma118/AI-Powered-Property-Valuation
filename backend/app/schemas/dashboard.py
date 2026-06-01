from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.property import Property


class DashboardSummary(BaseModel):
    properties_analyzed: int = 0
    avg_valuation: float | None = None
    saved_count: int = 0
    new_opportunities: int = 0
    recent: list[Property] = Field(default_factory=list)


class RecommendationsResponse(BaseModel):
    recommendations: list[Property] = Field(default_factory=list)
