from fastapi import APIRouter, Depends

from app.ai.analytics_service import AnalyticsService
from app.api.dependencies import get_analytics_service
from app.schemas.ai import AskRequest, AskResponse

router = APIRouter(prefix="/api/ai", tags=["IA Analytics"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, service: AnalyticsService = Depends(get_analytics_service)):
    return await service.ask(request)

