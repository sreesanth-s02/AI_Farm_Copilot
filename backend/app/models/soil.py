from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SoilReading(Base):
    __tablename__ = "soil_readings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    nitrogen: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    phosphorus: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    potassium: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    ph: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    moisture: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    organic_carbon: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    field: Mapped["Field"] = relationship(
        back_populates="soil_readings"
    )