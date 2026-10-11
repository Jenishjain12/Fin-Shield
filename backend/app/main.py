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

settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FIN-SHIELD", version="0.1.0")
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
