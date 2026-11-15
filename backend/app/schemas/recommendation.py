
from typing import Any
from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    field_id: int
    target_season: str
    target_year: int
    include_explanation: bool = True


class RecommendationResponse(BaseModel):
    field_id: int
    recommendations: list[dict[str, Any]]
    source: str
    generated_at: str
    explanation: str | None = None
