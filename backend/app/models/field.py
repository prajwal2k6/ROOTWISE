
from datetime import datetime

from sqlalchemy import (
    String, Float, Integer, ForeignKey, DateTime, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="RESTRICT"), index=True
    )
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.id", ondelete="SET NULL"), index=True
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    boundary_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)
    centroid_lat: Mapped[float | None] = mapped_column(Float)
    centroid_lon: Mapped[float | None] = mapped_column(Float)
    area_hectares: Mapped[float] = mapped_column(Float, nullable=False)

    soil_type: Mapped[str | None] = mapped_column(String(100))
    soil_ph: Mapped[float | None] = mapped_column(Float)
    irrigation_type: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    region: Mapped["Region"] = relationship(back_populates="fields")
    farmer: Mapped["Farmer | None"] = relationship(back_populates="fields")
    rotations: Mapped[list["FarmRotation"]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )
    climate_features: Mapped[list["ClimateFeature"]] = relationship(
        back_populates="field"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )
