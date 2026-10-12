from __future__ import annotations

from unittest.mock import patch

from PIL import Image

from tests.conftest import analyze_text
from tests.test_ocr import create_synthetic_image


def test_a_suspicious_investment_advertisement(client):
    """TEST A: Suspicious investment advertisement containing advertised monthly return,
    deposit bonus, and regulatory registration claim.

    Expected: Relevant indicators are detected, supporting text is returned, and the
    score is calculated according to documented rules.
    """
    response = client.post(
        "/api/analyze",
        data={
            "text": "TradeVista: Earn 20% monthly returns on automated trading! Deposit $250 today and get a $500 welcome bonus. SEBI and FCA registered broker.",
            "source": "social",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Risk score elevated (24 for high return + 16 for bonus + 12 for regulatory = 52)
    assert data["risk_score"] >= 50
    assert data["risk_category"] in {"HIGH", "CRITICAL"}

    signal_types = {sig["signal_type"] for sig in data["signals"]}
    assert "high_return_claim" in signal_types
    assert "deposit_incentive" in signal_types
    assert "regulatory_claim" in signal_types

    for sig in data["signals"]:
        assert sig["title"]
        assert sig["explanation"]
        assert sig["evidence"]
        assert sig["contribution"] > 0
        assert sig["recommendation"]

    # Content anomaly detected (20% monthly is extreme return)
    anomaly_types = {a["anomaly_type"] for a in data.get("anomalies", [])}
    assert "extreme_return_claim" in anomaly_types


def test_b_ordinary_financial_advertisement(client):
    """TEST B: Ordinary financial advertisement containing neutral investment information.

    Expected: No unsupported findings are generated; score is low.
    """
    response = client.post(
        "/api/analyze",
        data={
            "text": "Attend our free retirement planning workshop covering diversification basics, index fund asset allocation, and budgeting. Past performance is not indicative of future results.",
            "source": "webinar",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["risk_score"] < 25
    assert data["risk_category"] == "LOW"
    assert data["signals"] == []
    assert data["anomalies"] == []


def test_c_ocr_only_evidence(client):
    """TEST C: OCR-only evidence where image contains text absent from manual text field.

    Expected: Extracted text reaches indicator detection and risk scoring.
    """
    img_bytes = create_synthetic_image("Guaranteed 15% monthly return. Call 9876543210. Deposit bonus 100%.")
    response = client.post(
        "/api/analyze",
        data={"text": ""},
        files={"image": ("ad_banner.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ocr_status"] == "extracted"
    assert data["ocr_text"] is not None
    assert data["risk_score"] >= 40
    signal_types = {sig["signal_type"] for sig in data["signals"]}
    assert "guaranteed_return" in signal_types or "deposit_incentive" in signal_types
    assert any(ent["entity_type"] == "phone" for ent in data["entities"])


def test_d_duplicate_evidence(client):
    """TEST D: Duplicate evidence appears in both manual text and OCR image text.

    Expected: Duplicate evidence does not inflate the score unintentionally.
    """
    ad_copy = "Guaranteed returns of 10% daily. Deposit bonus on first funding."
    img_bytes = create_synthetic_image(ad_copy)

    res = client.post(
        "/api/analyze",
        data={"text": ad_copy},
        files={"image": ("duplicate.png", img_bytes, "image/png")},
    )
    assert res.status_code == 200
    data = res.json()

    # The expected indicators: guaranteed_return (28), high_return_claim (24), deposit_incentive (16) = 68.
    # If duplicate evidence was double-counted across text and OCR, score would be inflated (68*2=136 -> 100).
    assert data["risk_score"] == 68

    # Each signal group appears at most once
    signal_types = [sig["signal_type"] for sig in data["signals"]]
    assert len(signal_types) == len(set(signal_types))
    assert "guaranteed_return" in signal_types
    assert "high_return_claim" in signal_types
    assert "deposit_incentive" in signal_types


def test_e_missing_data(client, tmp_path):
    """TEST E: An image is uploaded but OCR produces no readable text.

    Expected: The system distinguishes unavailable evidence from a low score.
    """
    blank_img = Image.new("RGB", (200, 200), color="white")
    blank_path = tmp_path / "blank.png"
    blank_img.save(blank_path, format="PNG")
    blank_bytes = blank_path.read_bytes()

    response = client.post(
        "/api/analyze",
        data={"text": ""},
        files={"image": ("blank.png", blank_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ocr_status"] == "empty"
    assert data["risk_score"] == 0
    # Must report missing data warning
    assert len(data.get("missing_data_warnings", [])) > 0
    assert any("no readable" in w.lower() for w in data["missing_data_warnings"])
    assert "inconclusive" in (data["recommendation"] or "").lower() or "coverage is limited" in (data["limitations"] or "").lower()


def test_f_related_advertisements(client, db):
    """TEST F: Two synthetic records share an identifier, while a third does not.

    Expected: The matching records are linked with an explanation of the shared
    identifier; the unrelated record is not linked.
    """
    # Create ad 1 and ad 2 sharing a phone number
    shared_phone = "+91 99887 76655"
    ad1 = analyze_text(db, f"Investment syndicate alpha. Call {shared_phone} to register. Capital at risk.")
    ad2 = analyze_text(db, f"Investment syndicate beta. WhatsApp {shared_phone} for onboarding desk.")
    # Create unrelated ad 3
    ad3 = analyze_text(db, "Accounting review services for freelance consultants. Call +91 91234 56789.")

    detail1 = client.get(f"/api/ads/{ad1.id}").json()
    rel_ad_ids = set()
    for rel in detail1["relationships"]:
        other = rel["target_ad_id"] if rel["source_ad_id"] == ad1.id else rel["source_ad_id"]
        rel_ad_ids.add(other)

    assert ad2.id in rel_ad_ids
    assert ad3.id not in rel_ad_ids

    matching_rel = next(
        r for r in detail1["relationships"]
        if (r["source_ad_id"] == ad2.id or r["target_ad_id"] == ad2.id)
    )
    assert matching_rel["relationship_type"] == "shared_phone"
    assert "shared" in matching_rel["explanation"].lower()


def test_g_api_contract(client):
    """TEST G: Verify that the backend response fields match what the frontend consumes."""
    response = client.post(
        "/api/analyze",
        data={
            "text": "TradeVista bonus! Guaranteed 25% returns monthly. Call +91 98765 00000. SEBI registered broker. Visit http://203.0.113.20/login",
            "source": "social",
            "source_url": "http://203.0.113.20/login",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Required top-level fields
    expected_fields = [
        "id",
        "risk_score",
        "risk_category",
        "analysis_status",
        "review_status",
        "text",
        "source",
        "source_url",
        "ocr_status",
        "recommendation",
        "limitations",
        "missing_data_warnings",
        "signals",
        "entities",
        "anomalies",
        "relationships",
        "notes",
    ]
    for field in expected_fields:
        assert field in data, f"Missing field in API response: {field}"

    # Verify signal contract
    for sig in data["signals"]:
        assert "id" in sig
        assert "signal_type" in sig
        assert "title" in sig
        assert "explanation" in sig
        assert "evidence" in sig
        assert "contribution" in sig

    # Verify anomaly contract
    for anomaly in data["anomalies"]:
        assert "id" in anomaly
        assert "anomaly_type" in anomaly
        assert "title" in anomaly
        assert "explanation" in anomaly
        assert "evidence" in anomaly
        assert "severity" in anomaly


def test_h_failure_handling(client):
    """TEST H: An internal scoring or anomaly-detection error occurs.

    Expected: The system reports an analysis failure instead of silently
    returning a successful zero-risk result.
    """
    with patch("app.services.analysis.assess_risk", side_effect=RuntimeError("Simulated internal scoring crash")):
        response = client.post(
            "/api/analyze",
            data={"text": "Guaranteed 20% return daily. Act now!"},
        )
        # Must fail with an HTTP error rather than returning 200 with score 0
        assert response.status_code >= 400
