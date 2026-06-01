from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.property import Property as PropertyModel
from app.models.saved import SavedProperty as SavedPropertyModel
from app.models.user import User as UserModel
from app.schemas.saved import SavedCreate, SavedProperty

router = APIRouter(prefix="/saved", tags=["saved"])


@router.get("", response_model=list[SavedProperty])
async def list_saved(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> list[SavedProperty]:
    rows = (
        await db.execute(
            select(SavedPropertyModel)
            .where(SavedPropertyModel.user_id == current_user.id)
            .options(
                selectinload(SavedPropertyModel.property).selectinload(
                    PropertyModel.neighborhood
                ),
                selectinload(SavedPropertyModel.property).selectinload(
                    PropertyModel.analysis
                ),
            )
            .order_by(SavedPropertyModel.created_at.desc())
        )
    ).scalars().all()

    return [SavedProperty.model_validate(r) for r in rows]


@router.post("", response_model=SavedProperty, status_code=status.HTTP_201_CREATED)
async def create_saved(
    payload: SavedCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> SavedProperty:
    # Validate the property exists.
    prop = (
        await db.execute(
            select(PropertyModel).where(PropertyModel.id == payload.property_id)
        )
    ).scalar_one_or_none()
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    # Idempotent on (user_id, property_id): update existing instead of duplicating.
    existing = (
        await db.execute(
            select(SavedPropertyModel).where(
                SavedPropertyModel.user_id == current_user.id,
                SavedPropertyModel.property_id == payload.property_id,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        if payload.notes is not None:
            existing.notes = payload.notes
        if payload.label is not None:
            existing.label = payload.label
        saved = existing
    else:
        saved = SavedPropertyModel(
            user_id=current_user.id,
            property_id=payload.property_id,
            notes=payload.notes,
            label=payload.label,
        )
        db.add(saved)

    await db.commit()

    # Reload with relationships eagerly populated for serialization.
    saved = (
        await db.execute(
            select(SavedPropertyModel)
            .where(SavedPropertyModel.id == saved.id)
            .options(
                selectinload(SavedPropertyModel.property).selectinload(
                    PropertyModel.neighborhood
                ),
                selectinload(SavedPropertyModel.property).selectinload(
                    PropertyModel.analysis
                ),
            )
        )
    ).scalar_one()

    return SavedProperty.model_validate(saved)


@router.delete("/{saved_id}")
async def delete_saved(
    saved_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    saved = (
        await db.execute(
            select(SavedPropertyModel).where(
                SavedPropertyModel.id == saved_id,
                SavedPropertyModel.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()

    if saved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved property not found.",
        )

    await db.delete(saved)
    await db.commit()
    return {"ok": True}
