
from datetime import date, datetime

from sqlalchemy import (
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClimateFeature(Base):
    __tablename__ = "climate_features"

    # Prevent duplicate climate observations for the same map cell,
    # data source and date.
    __table_args__ = (
        Index(
            "uq_climate_map_cell_source_date",
            "map_cell_id",
            "source",
            "feature_date",
            unique=True,
            postgresql_where=text("map_cell_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    region_id: Mapped[int | None] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"),
        index=True,
    )

    field_id: Mapped[int | None] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"),
        index=True,
    )

    map_cell_id: Mapped[int | None] = mapped_column(
        ForeignKey("map_cells.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(String(100), nullable=False)

    feature_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    rainfall_mm: Mapped[float | None] = mapped_column(Float)
    temperature_min_c: Mapped[float | None] = mapped_column(Float)
    temperature_max_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    soil_moisture_pct: Mapped[float | None] = mapped_column(Float)
    ndvi: Mapped[float | None] = mapped_column(Float)
    evapotranspiration_mm: Mapped[float | None] = mapped_column(Float)

    data_quality: Mapped[str | None] = mapped_column(String(50))

    source_metadata: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    region: Mapped["Region | None"] = relationship(
        back_populates="climate_features"
    )

    field: Mapped["Field | None"] = relationship(
        back_populates="climate_features"
    )
