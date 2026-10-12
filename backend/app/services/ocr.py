from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

logger = logging.getLogger("finshield.ocr")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class OcrResult:
    text: str | None
    status: str
    limitation: str | None = None


@dataclass
class OcrEngineStatus:
    available: bool
    engine: str = "tesseract"
    version: str | None = None
    tesseract_path: str | None = None
    languages: list[str] = field(default_factory=list)
    error: str | None = None


def resolve_tesseract_cmd() -> str | None:
    """Resolve the Tesseract binary path from settings, environment, or system PATH."""
    settings = get_settings()
    configured = settings.tesseract_cmd or os.environ.get("TESSERACT_CMD")
    if configured:
        resolved = shutil.which(configured) or configured
        if Path(resolved).is_file() and os.access(resolved, os.X_OK):
            return str(resolved)
    found = shutil.which("tesseract")
    if found:
        return str(found)
    return None


def get_ocr_engine_status() -> OcrEngineStatus:
    """Check if the OCR engine and its language data are available in the current environment."""
    try:
        import pytesseract
    except ImportError:
        logger.warning("OCR engine status check: pytesseract package is not installed.")
        return OcrEngineStatus(
            available=False,
            error="pytesseract is not installed.",
        )

    tesseract_bin = resolve_tesseract_cmd()
    if tesseract_bin:
        pytesseract.pytesseract.tesseract_cmd = tesseract_bin

    try:
        version_str = str(pytesseract.get_tesseract_version())
    except Exception as exc:
        logger.warning(
            "OCR engine status check: Tesseract executable not accessible (%s: %s)",
            exc.__class__.__name__,
            exc,
        )
        return OcrEngineStatus(
            available=False,
            tesseract_path=tesseract_bin,
            error=f"Tesseract executable not found or failed to execute ({exc.__class__.__name__}).",
        )

    try:
        langs = pytesseract.get_languages()
    except Exception as exc:
        logger.warning("OCR engine status check: Failed to retrieve language files (%s: %s)", exc.__class__.__name__, exc)
        langs = []

    logger.info(
        "OCR engine status check: available=True, path=%s, version=%s, languages=%s",
        tesseract_bin or "default PATH",
        version_str,
        langs,
    )
    return OcrEngineStatus(
        available=True,
        version=version_str,
        tesseract_path=tesseract_bin,
        languages=langs,
    )


def validate_image(filename: str, content_type: str | None, size: int, max_bytes: int) -> str | None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return "Unsupported file type. Upload a JPEG, PNG, or WebP image."
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        return "Unsupported content type. Upload a JPEG, PNG, or WebP image."
    if size <= 0:
        return "Uploaded file is empty."
    if size > max_bytes:
        return f"File exceeds the {max_bytes // (1024 * 1024)} MB limit."
    return None


def inspect_image_file(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        return "The uploaded file could not be read as an image."
    return None


def extract_text_from_image(path: Path) -> OcrResult:
    """Extract text from an image using Tesseract OCR.

    Returns an explicit status and limitation string. Never silently treats
    engine or execution failures as an image containing no text.
    """
    file_size = path.stat().st_size if path.exists() else 0
    logger.info("Attempting OCR for image '%s' (%d bytes)", path.name, file_size)

    try:
        import pytesseract  # type: ignore
    except ImportError:
        logger.warning("OCR skipped for '%s': pytesseract package is not installed.", path.name)
        return OcrResult(
            text=None,
            status="unavailable",
            limitation="OCR is unavailable because pytesseract is not installed. Text analysis still works if advertisement copy is provided.",
        )

    tesseract_bin = resolve_tesseract_cmd()
    if tesseract_bin:
        pytesseract.pytesseract.tesseract_cmd = tesseract_bin

    try:
        _ = pytesseract.get_tesseract_version()
    except Exception as exc:
        logger.warning("OCR skipped for '%s': Tesseract binary unavailable (%s)", path.name, exc.__class__.__name__)
        return OcrResult(
            text=None,
            status="unavailable",
            limitation=f"OCR is unavailable because Tesseract OCR engine is not installed or not in PATH ({exc.__class__.__name__}). Text analysis still works if advertisement copy is provided.",
        )

    try:
        with Image.open(path) as image:
            text = pytesseract.image_to_string(image).strip()
    except Exception as exc:
        logger.error("OCR execution failed for '%s' (%s): %s", path.name, exc.__class__.__name__, str(exc))
        return OcrResult(
            text=None,
            status="failed",
            limitation=f"OCR could not be completed ({exc.__class__.__name__}). Provide advertisement text for analysis.",
        )

    if not text:
        logger.info("OCR completed for '%s': no readable text extracted (empty)", path.name)
        return OcrResult(
            text=None,
            status="empty",
            limitation="OCR completed but extracted no readable text from the image.",
        )

    logger.info("OCR successful for '%s': extracted %d characters", path.name, len(text))
    return OcrResult(text=text, status="extracted")

