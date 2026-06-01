import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.property import Property


class Analysis(Base):
    __tablename__ = "analyses"

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
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pros: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    cons: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    investment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[str | None] = mapped_column(String(20), nullable=True)
    buyer_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    property: Mapped["Property"] = relationship(back_populates="analysis")
