"""Pydantic v2 request/response schemas, re-exported for convenient imports."""

from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.schemas.dashboard import DashboardSummary, RecommendationsResponse
from app.schemas.property import (
    ComparablesResponse,
    ComparablesStats,
    Property,
    PropertyAnalysis,
    PropertyNeighborhood,
    SearchResponse,
)
from app.schemas.saved import SavedCreate, SavedProperty
from app.schemas.user import LoginRequest, RegisterRequest, Token, User

__all__ = [
    # user
    "User",
    "RegisterRequest",
    "LoginRequest",
    "Token",
    # property
    "Property",
    "PropertyNeighborhood",
    "PropertyAnalysis",
    "SearchResponse",
    "ComparablesResponse",
    "ComparablesStats",
    # dashboard
    "DashboardSummary",
    "RecommendationsResponse",
    # chat
    "ChatRequest",
    "ChatResponse",
    "ChatSource",
    # saved
    "SavedCreate",
    "SavedProperty",
]
