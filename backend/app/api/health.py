from fastapi import APIRouter

from app.schemas.common import HealthOut
from app.services.ocr import get_ocr_engine_status

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    engine_status = get_ocr_engine_status()
    return HealthOut(
        status="ok",
        service="FIN-SHIELD",
        dataset="synthetic demonstration data plus investigator submissions",
        ocr_available=engine_status.available,
        ocr_engine=engine_status.engine if engine_status.available else None,
        ocr_languages=engine_status.languages,
    )
