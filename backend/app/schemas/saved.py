from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.property import Property


class SavedCreate(BaseModel):
    property_id: UUID
    notes: str | None = None
    label: str | None = Field(default=None, max_length=64)


class SavedProperty(BaseModel):
    """A user's saved property, with the embedded property detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    property_id: UUID
    notes: str | None = None
    label: str | None = None
    created_at: datetime

    property: Property | None = None
