from pydantic import BaseModel, Field

from app.schemas.dashboard import DashboardFilters


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    filters: DashboardFilters = Field(default_factory=DashboardFilters)


class AskResponse(BaseModel):
    answer: str
    intent: str
    visualization: str | None = None
    value_format: str = "currency"
    data: list[dict] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    used_ai: bool = False
