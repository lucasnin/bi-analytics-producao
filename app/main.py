import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import ai, dashboard, imports
from app.core.config import get_settings

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bi-analytics")

app = FastAPI(title=settings.app_name, version="0.1.0", description="Camada segura de BI e analytics com IA local opcional")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(imports.router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", extra={"request_id": request_id})
        return JSONResponse(status_code=500, content={"detail": "Não foi possível concluir a solicitação", "request_id": request_id})
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    logger.info("request_complete method=%s path=%s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, (time.perf_counter()-started)*1000)
    return response


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "data_provider": settings.data_provider, "ai_provider": settings.ai_provider}


@app.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "app_name": settings.app_name})
