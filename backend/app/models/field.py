from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id"),
        nullable=False,
        index=True
    )

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    area_acres: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    soil_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    farm = relationship(
        "Farm",
        back_populates="fields"
    )

    crops = relationship(
        "Crop",
        back_populates="field",
        cascade="all, delete-orphan"
    )

    soil_readings: Mapped[list["SoilReading"]] = relationship(
    back_populates="field",
    cascade="all, delete-orphan"
    )