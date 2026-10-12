from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id"),
        nullable=False,
        index=True
    )

    farm_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    village: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    total_area_acres: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    farmer = relationship(
        "Farmer",
        back_populates="farms"
    )

    fields = relationship(
        "Field",
        back_populates="farm",
        cascade="all, delete-orphan"
    )