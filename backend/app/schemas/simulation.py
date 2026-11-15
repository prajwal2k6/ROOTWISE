
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class SimulationCreate(BaseModel):
    field_id: int
    title: str
    description: str | None = None
    input_parameters: dict[str, Any] = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    id: int
    field_id: int
    farmer_id: int | None
    title: str
    description: str | None
    input_parameters: dict[str, Any]
    result: dict[str, Any] | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
