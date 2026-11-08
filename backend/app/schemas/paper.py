from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaperCreate(BaseModel):
    title: str = Field(min_length=1)
    authors: str | None = None
    abstract: str | None = None
    doi: str | None = None
    publication_year: int | None = Field(
        default=None, ge=1500, le=2100
    )
    source: str | None = None
    pdf_path: str | None = None


class PaperResponse(PaperCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime