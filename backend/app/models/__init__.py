"""Import all models so that Base.metadata is fully populated.

Importing this package (or any submodule) registers every ORM model with the
shared DeclarativeBase, which is required before Base.metadata.create_all().
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
