from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True
    )

    preferred_language: Mapped[str] = mapped_column(
        Enum("ta", "en", name="language_enum"),
        default="ta",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    farms = relationship(
        "Farm",
        back_populates="farmer",
        cascade="all, delete-orphan"
    )