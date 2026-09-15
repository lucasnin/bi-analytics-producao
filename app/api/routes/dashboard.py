from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_dashboard_service
from app.core.config import get_settings
from app.schemas.dashboard import DashboardFilters, DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def filters_dependency(
    start_date: str | None = Query(None), end_date: str | None = Query(None),
    management: str | None = None, manual_management: str | None = None, team: str | None = None, operator: str | None = None,
    product: str | None = None, modality: str | None = None, agreement: str | None = None,
    status: str | None = None,
) -> DashboardFilters:
    return DashboardFilters(start_date=start_date, end_date=end_date, management=management, manual_management=manual_management, team=team,
                            operator=operator, product=product, modality=modality, agreement=agreement, status=status)


@router.get("/resumo", response_model=DashboardResponse)
def summary(filters: DashboardFilters = Depends(filters_dependency), service: DashboardService = Depends(get_dashboard_service)):
    data = service.dashboard(filters)
    return {key: data[key] for key in ("kpis", "daily", "accumulated", "teams", "operators", "managements", "statuses", "daily_by_status", "monthly", "insights", "story", "analytics")} | {"source": get_settings().data_provider}


@router.get("/projecao")
def projection(filters: DashboardFilters = Depends(filters_dependency), service: DashboardService = Depends(get_dashboard_service)):
    return service.dashboard(filters)["projection"]
