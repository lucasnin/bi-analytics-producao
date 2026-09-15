from functools import lru_cache

from app.ai.analytics_service import AnalyticsService
from app.ai.ollama_provider import OllamaProvider
from app.core.config import get_settings
from app.repositories.dashboard_repository import DemoDashboardRepository, MySQLDashboardRepository
from app.repositories.csv_production_repository import CsvProductionRepository
from app.services.dashboard_service import DashboardService


@lru_cache
def get_dashboard_service() -> DashboardService:
    settings = get_settings()
    if settings.data_provider == "mysql":
        repository = MySQLDashboardRepository()
    elif settings.data_provider == "csv":
        repository = CsvProductionRepository(settings.csv_production_path)
    else:
        repository = DemoDashboardRepository()
    return DashboardService(repository)


@lru_cache
def get_analytics_service() -> AnalyticsService:
    settings = get_settings()
    provider = OllamaProvider(settings.ollama_base_url, settings.ollama_model) if settings.ai_provider == "ollama" else None
    return AnalyticsService(get_dashboard_service(), provider)
