
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
