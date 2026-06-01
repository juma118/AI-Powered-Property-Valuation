from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.analysis import Analysis as AnalysisModel
from app.models.property import Property as PropertyModel
from app.models.saved import SavedProperty as SavedPropertyModel
from app.models.user import User as UserModel
from app.schemas.dashboard import DashboardSummary, RecommendationsResponse
from app.schemas.property import Property

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def summary(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> DashboardSummary:
    properties_analyzed = (
        await db.execute(select(func.count()).select_from(AnalysisModel))
    ).scalar_one()

    avg_valuation = (
        await db.execute(select(func.avg(AnalysisModel.estimated_value)))
    ).scalar_one_or_none()

    saved_count = (
        await db.execute(
            select(func.count())
            .select_from(SavedPropertyModel)
            .where(SavedPropertyModel.user_id == current_user.id)
        )
    ).scalar_one()

    # "New opportunities": high-investment-score properties.
    new_opportunities = (
        await db.execute(
            select(func.count())
            .select_from(AnalysisModel)
            .where(AnalysisModel.investment_score >= 75)
        )
    ).scalar_one()

    recent_rows = (
        await db.execute(
            select(PropertyModel)
            .options(
                selectinload(PropertyModel.neighborhood),
                selectinload(PropertyModel.analysis),
            )
            .order_by(PropertyModel.created_at.desc())
            .limit(6)
        )
    ).scalars().all()

    return DashboardSummary(
        properties_analyzed=int(properties_analyzed or 0),
        avg_valuation=float(avg_valuation) if avg_valuation is not None else None,
        saved_count=int(saved_count or 0),
        new_opportunities=int(new_opportunities or 0),
        recent=[Property.model_validate(p) for p in recent_rows],
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> RecommendationsResponse:
    # Prefer properties with the highest investment score.
    scored_rows = (
        await db.execute(
            select(PropertyModel)
            .join(AnalysisModel, AnalysisModel.property_id == PropertyModel.id)
            .options(
                selectinload(PropertyModel.neighborhood),
                selectinload(PropertyModel.analysis),
            )
            .order_by(AnalysisModel.investment_score.desc())
            .limit(6)
        )
    ).scalars().all()

    rows = list(scored_rows)

    # Fall back to recent listings if no analyses exist yet.
    if not rows:
        rows = list(
            (
                await db.execute(
                    select(PropertyModel)
                    .options(
                        selectinload(PropertyModel.neighborhood),
                        selectinload(PropertyModel.analysis),
                    )
                    .order_by(PropertyModel.created_at.desc())
                    .limit(6)
                )
            ).scalars().all()
        )

    return RecommendationsResponse(
        recommendations=[Property.model_validate(p) for p in rows]
    )
