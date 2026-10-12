import io
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from app.services.ocr import extract_text_from_image, get_ocr_engine_status, OcrResult


def create_synthetic_image(text: str) -> bytes:
    """Generate a simple synthetic image containing legible black text on a white background."""
    img = Image.new("RGB", (600, 150), color="white")
    draw = ImageDraw.Draw(img)
    # Draw plain text with margins
    draw.text((20, 40), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_ocr_engine_availability():
    """Verify that OCR engine status inspection reports engine availability, version, and language support."""
    status = get_ocr_engine_status()
    assert status.engine == "tesseract"
    # When tesseract is installed in test environment, it should be available
    assert status.available is True
    assert status.version is not None
    assert "eng" in status.languages


def test_ocr_extraction_synthetic_image(tmp_path: Path):
    """Verify OCR extracts text from a readable synthetic advertisement image."""
    img_bytes = create_synthetic_image("Guaranteed 20% daily return. Call 9876543210")
    img_path = tmp_path / "test_ad.png"
    img_path.write_bytes(img_bytes)

    result = extract_text_from_image(img_path)
    assert result.status == "extracted"
    assert result.text is not None
    assert "Guaranteed" in result.text
    assert "9876543210" in result.text
    assert result.limitation is None


def test_ocr_empty_image(tmp_path: Path):
    """Verify that an image with no text returns 'empty' status and an honest limitation."""
    img = Image.new("RGB", (200, 200), color="white")
    img_path = tmp_path / "blank.png"
    img.save(img_path, format="PNG")

    result = extract_text_from_image(img_path)
    assert result.status == "empty"
    assert result.text is None
    assert result.limitation is not None
    assert "no readable text" in result.limitation.lower()


def test_image_upload_through_api(client):
    """Verify image upload through /api/analyze endpoint with OCR extraction and schema response."""
    img_bytes = create_synthetic_image("Guaranteed returns. Pay advance fee to scam@okaxis. Call 9876543210")
    response = client.post(
        "/api/analyze",
        data={"source": "flyer"},
        files={"image": ("scam_flyer.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ocr_status"] == "extracted"
    assert data["ocr_text"] is not None
    assert "Guaranteed" in data["ocr_text"]
    # Check that OCR text reached risk scoring
    assert data["risk_score"] >= 50
    assert any(sig["signal_type"] == "guaranteed_return" for sig in data["signals"])
    assert any(ent["entity_type"] == "phone" for ent in data["entities"])


def test_integration_of_ocr_text_with_risk_scoring(client):
    """Verify that text extracted exclusively from an image reaches the risk engine and elevates the score."""
    # When text field is empty, but image contains high-risk advertisement copy
    img_bytes = create_synthetic_image("Guaranteed returns daily! Double your money. Urgent payout window closing!")
    response = client.post(
        "/api/analyze",
        data={"text": ""},
        files={"image": ("high_risk_ad.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ocr_status"] == "extracted"
    # Signals must be detected from the image OCR
    signal_types = [sig["signal_type"] for sig in data["signals"]]
    assert "guaranteed_return" in signal_types
    assert data["risk_score"] > 20


def test_graceful_handling_when_ocr_engine_unavailable(client, tmp_path: Path):
    """Verify graceful handling and honest limitation reporting when OCR engine is unavailable."""
    # Test service level
    img_path = tmp_path / "ad.png"
    img_path.write_bytes(create_synthetic_image("Some sample text"))

    with patch("app.services.ocr.resolve_tesseract_cmd", return_value="/nonexistent/tesseract"):
        with patch("pytesseract.get_tesseract_version", side_effect=Exception("Binary not found")):
            result = extract_text_from_image(img_path)
            assert result.status == "unavailable"
            assert result.text is None
            assert result.limitation is not None
            assert "unavailable" in result.limitation.lower()

    # Test API level with fallback to provided text
    with patch("app.services.analysis.extract_text_from_image") as mock_extract:
        mock_extract.return_value = OcrResult(
            text=None,
            status="unavailable",
            limitation="OCR is unavailable because Tesseract OCR engine is not installed.",
        )
        response = client.post(
            "/api/analyze",
            data={"text": "Educational webinar about portfolio allocation."},
            files={"image": ("flyer.png", create_synthetic_image("Some flyer"), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ocr_status"] == "unavailable"
        assert data["ocr_text"] is None
        assert "OCR is unavailable" in (data["limitations"] or "")


def test_graceful_handling_when_pytesseract_not_imported(tmp_path: Path):
    """Verify handling when pytesseract package import fails."""
    img_path = tmp_path / "ad.png"
    img_path.write_bytes(create_synthetic_image("Some sample text"))

    with patch.dict("sys.modules", {"pytesseract": None}):
        result = extract_text_from_image(img_path)
        assert result.status == "unavailable"
        assert result.text is None
        assert "pytesseract is not installed" in (result.limitation or "")


def test_health_reports_ocr_status(client):
    """Verify /api/health endpoint includes OCR availability information."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ocr_available" in data
    assert data["ocr_available"] is True
    assert data["ocr_engine"] == "tesseract"
