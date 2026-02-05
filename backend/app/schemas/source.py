from datetime import datetime
from pydantic import BaseModel, HttpUrl


class SourceCreateRequest(BaseModel):
    url: HttpUrl
    platform: str | None = None  # auto-detected if not provided


class SourceResponse(BaseModel):
    id: str
    platform: str
    source_url: str
    status: str
    is_confirmed: bool
    parsed_data: dict | None
    last_scraped_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourcePreviewResponse(BaseModel):
    id: str
    platform: str
    source_url: str
    parsed_data: dict | None
    data_quality: str | None
