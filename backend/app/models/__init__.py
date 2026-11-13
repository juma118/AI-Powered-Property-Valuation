"""Import all models so that Base.metadata is fully populated.
"""

from app.models.user import User
from app.models.property import Property
from app.models.neighborhood import Neighborhood
from app.models.analysis import Analysis
from app.models.saved import SavedProperty

__all__ = [
    "User",
    "Property",
    "Neighborhood",
    "Analysis",
    "SavedProperty",
]
