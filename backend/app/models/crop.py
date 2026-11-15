
from sqlalchemy import String, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    scientific_name: Mapped[str | None] = mapped_column(String(150))

    season: Mapped[str | None] = mapped_column(String(100))
    duration_days: Mapped[int | None] = mapped_column(Integer)
    water_requirement: Mapped[str | None] = mapped_column(String(50))

    water_requirement_mm: Mapped[float | None] = mapped_column(Float)
    soil_preferences: Mapped[dict | None] = mapped_column(JSONB)
    nutrient_needs: Mapped[dict | None] = mapped_column(JSONB)
    crop_metadata: Mapped[dict | None] = mapped_column(JSONB)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    rotations: Mapped[list["FarmRotation"]] = relationship(
        back_populates="crop"
    )
