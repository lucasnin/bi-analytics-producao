import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.dependencies import get_analytics_service, get_dashboard_service
from app.core.config import get_settings
from app.repositories.csv_production_repository import CsvProductionRepository, REQUIRED_COLUMNS

router = APIRouter(prefix="/api/imports", tags=["Importação"])


@router.get("/production")
def production_import_status():
    settings = get_settings()
    repository = CsvProductionRepository(settings.csv_production_path)
    try:
        return {"available": True, **repository.metadata()}
    except RuntimeError:
        return {"available": False}


@router.get("/production/filters")
def production_filter_options():
    settings = get_settings()
    return CsvProductionRepository(settings.csv_production_path).filter_options()


@router.post("/production")
async def import_production(file: UploadFile = File(...)):
    settings = get_settings()
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Envie um arquivo CSV")
    target = Path(settings.csv_production_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".uploading")
    size = 0
    try:
        with temporary.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.csv_max_upload_mb * 1024 * 1024:
                    raise HTTPException(413, "Arquivo maior que o limite configurado")
                output.write(chunk)
        CsvProductionRepository(str(temporary)).metadata()
        os.replace(temporary, target)
        get_dashboard_service.cache_clear()
        get_analytics_service.cache_clear()
        return CsvProductionRepository(str(target)).metadata()
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "O CSV deve usar codificação UTF-8") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        await file.close()
        if temporary.exists():
            temporary.unlink()
