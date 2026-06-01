import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, Float, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

if TYPE_CHECKING:
    from app.models.neighborhood import Neighborhood
    from app.models.analysis import Analysis
    from app.models.saved import SavedProperty


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255), index=True, nullable=True
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    zip: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    beds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photos: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", server_default="active"
    )
    listed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # lazy="selectin" so these load eagerly within the async session — required
    # because Pydantic serialization (Property.model_validate) accesses them
    # outside the await context, which would otherwise raise MissingGreenlet.
    neighborhood: Mapped[Optional["Neighborhood"]] = relationship(
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    analysis: Mapped[Optional["Analysis"]] = relationship(
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    saved_by: Mapped[List["SavedProperty"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
    )
