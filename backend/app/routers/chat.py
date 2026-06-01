from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.schemas.property import Property
from app.services import property_service
from app.services.ai_service import AIService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
async def query(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    # Retrieve relevant properties via semantic (vector) search.
    matches = await property_service.semantic_search(db, payload.query, limit=5)

    context_props = []
    properties: list[Property] = []
    sources: list[ChatSource] = []
    for item in matches:
        # semantic_search returns (property, score) pairs (or bare properties).
        if isinstance(item, tuple):
            prop, score = item[0], item[1]
        else:
            prop, score = item, 1.0

        context_props.append(prop)
        properties.append(Property.model_validate(prop))
        sources.append(
            ChatSource(
                property_id=prop.id,
                address=prop.address,
                score=float(score),
            )
        )

    ai = AIService()
    answer = await ai.chat(payload.query, context_props)

    return ChatResponse(answer=answer, properties=properties, sources=sources)
