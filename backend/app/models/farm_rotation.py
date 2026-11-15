
from datetime import date, datetime

from sqlalchemy import (
    String, Integer, Float, Date, DateTime,
    ForeignKey, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FarmRotation(Base):
    __tablename__ = "farm_rotations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), index=True
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), index=True
    )

    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    planting_date: Mapped[date | None] = mapped_column(Date)
    harvest_date: Mapped[date | None] = mapped_column(Date)

    yield_tonnes: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(
        String(50), default="completed"
    )
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    field: Mapped["Field"] = relationship(back_populates="rotations")
    crop: Mapped["Crop"] = relationship(back_populates="rotations")
