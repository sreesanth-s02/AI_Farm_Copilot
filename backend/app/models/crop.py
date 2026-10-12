from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id"),
        nullable=False,
        index=True
    )

    crop_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    variety: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    sowing_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    expected_harvest_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    growth_stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False
    )

    field = relationship(
        "Field",
        back_populates="crops"
    )