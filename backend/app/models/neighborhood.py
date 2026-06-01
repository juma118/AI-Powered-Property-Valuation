import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.property import Property


class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    school_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    restaurants_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commute_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    walk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crime_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearby_schools: Mapped[List[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    property: Mapped["Property"] = relationship(back_populates="neighborhood")
