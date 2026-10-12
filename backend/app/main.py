import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import ads, alerts, analyze, campaigns, dashboard, health
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import Alert, AnalystNote, Advertisement, AdvertisementRelationship, ExtractedEntity, RiskSignal  # noqa: F401
from app.services.ocr import get_ocr_engine_status

settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    ocr_status = get_ocr_engine_status()
    logging.getLogger("finshield.startup").info(
        "FIN-SHIELD starting up. OCR available: %s (path: %s, version: %s, langs: %s)",
        ocr_status.available,
        ocr_status.tesseract_path or "PATH",
        ocr_status.version or "N/A",
        ocr_status.languages,
    )
    try:
        from app.db.session import SessionLocal
        from seed import seed
        with SessionLocal() as db:
            created = seed(db)
            if created:
                logging.getLogger("finshield.startup").info("Seeded %d synthetic demonstration records on startup.", created)
    except Exception as exc:
        logging.getLogger("finshield.startup").warning("Auto-seed on startup: %s", exc)
    yield


app = FastAPI(title="FIN-SHIELD", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ads.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")

app.mount("/uploads", StaticFiles(directory=settings.upload_dir, check_dir=False), name="uploads")


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})
