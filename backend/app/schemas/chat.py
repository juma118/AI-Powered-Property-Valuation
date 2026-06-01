from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.property import Property


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class ChatSource(BaseModel):
    property_id: UUID
    address: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    properties: list[Property] = Field(default_factory=list)
    sources: list[ChatSource] = Field(default_factory=list)
