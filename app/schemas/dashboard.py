from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class DashboardFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    management: str | None = Field(None, max_length=80)
    manual_management: str | None = Field(None, max_length=80)
    team: str | None = Field(None, max_length=80)
    operator: str | None = Field(None, max_length=80)
    product: str | None = Field(None, max_length=80)
    modality: str | None = Field(None, max_length=80)
    agreement: str | None = Field(None, max_length=80)
    status: str | None = Field(None, max_length=40)

    @model_validator(mode="after")
    def validate_period(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("A data inicial deve ser anterior à data final")
        return self


class KPI(BaseModel):
    key: str
    label: str
    value: Decimal
    format: str = "currency"
    change: float | None = None


class DataPoint(BaseModel):
    label: str
    value: Decimal


class DashboardResponse(BaseModel):
    kpis: list[KPI]
    daily: list[DataPoint]
    accumulated: list[DataPoint]
    teams: list[DataPoint]
    operators: list[DataPoint]
    managements: list[DataPoint]
    statuses: list[DataPoint]
    daily_by_status: dict[str, list[Decimal]] = Field(default_factory=dict)
    monthly: list[dict] = Field(default_factory=list)
    insights: list[dict]
    story: list[str] = Field(default_factory=list)
    analytics: dict = Field(default_factory=dict)
    source: str
