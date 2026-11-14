
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.sql import func

from app.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)

    # Supabase user ownership
    supabase_user_id = Column(String(36), index=True, nullable=False)

    # Farm identity
    farm_name = Column(String(150), nullable=False, default="My Farm")

    # Farm location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    boundary = Column(JSON, nullable=False)

    # Farm area
    area_acres = Column(Float, nullable=False)
    area_hectares = Column(Float, nullable=False)

    # Farm profile
    soil_type = Column(String(100), nullable=True)
    irrigation = Column(String(100), nullable=True)

    main_crop = Column(String(150), nullable=True)
    other_crops = Column(Text, nullable=True)

    sowing_season = Column(String(100), nullable=True)
    harvest_period = Column(String(100), nullable=True)

    previous_crop_sequence = Column(Text, nullable=True)
    crop_frequency = Column(String(100), nullable=True)

    priority = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
