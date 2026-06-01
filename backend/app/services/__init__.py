"""Service layer: external clients + business logic.

Exposes the external API clients and the property business-logic functions
used by the routers. All public functions/clients here are import-safe even
when external API keys are absent (mock fallbacks are used).
"""

from app.services.rentcast_client import RentCastClient
from app.services.enrichment_service import EnrichmentService
from app.services.ai_service import AIService
from app.services import property_service

__all__ = [
    "RentCastClient",
    "EnrichmentService",
    "AIService",
    "property_service",
]
