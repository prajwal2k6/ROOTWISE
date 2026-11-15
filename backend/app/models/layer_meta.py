
from datetime import date, datetime

from sqlalchemy import (
    String, Date, DateTime, Boolean, func, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LayerMeta(Base):
    __tablename__ = "layers_meta"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    layer_key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    data_source: Mapped[str] = mapped_column(String(150), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))

    min_date: Mapped[date | None] = mapped_column(Date)
    max_date: Mapped[date | None] = mapped_column(Date)

    style: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
