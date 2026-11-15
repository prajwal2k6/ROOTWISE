
from datetime import date, datetime

from sqlalchemy import (
    String, Float, Date, DateTime, ForeignKey,
    UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MapCell(Base):
    __tablename__ = "map_cells"

    __table_args__ = (
        UniqueConstraint("region_id", "cell_code", name="uq_region_cell"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"), index=True
    )

    cell_code: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)

    centroid_lat: Mapped[float | None] = mapped_column(Float)
    centroid_lon: Mapped[float | None] = mapped_column(Float)

    risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(50))
    source_date: Mapped[date | None] = mapped_column(Date)

    properties: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    region: Mapped["Region"] = relationship(back_populates="map_cells")
