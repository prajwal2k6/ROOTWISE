
from datetime import datetime

from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    district: Mapped[str | None] = mapped_column(String(150))
    state: Mapped[str] = mapped_column(String(100), default="Karnataka")
    country: Mapped[str] = mapped_column(String(100), default="India")

    boundary_geojson: Mapped[dict | None] = mapped_column(JSONB)
    centroid_lat: Mapped[float | None] = mapped_column(Float)
    centroid_lon: Mapped[float | None] = mapped_column(Float)
    area_hectares: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fields: Mapped[list["Field"]] = relationship(back_populates="region")
    climate_features: Mapped[list["ClimateFeature"]] = relationship(
        back_populates="region"
    )
    map_cells: Mapped[list["MapCell"]] = relationship(back_populates="region")
