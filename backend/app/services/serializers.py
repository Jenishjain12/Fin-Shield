from sqlalchemy.orm import Session

from app.models import Advertisement, AdvertisementRelationship
from app.schemas.common import AdvertisementDetail, AdvertisementSummary, RelationshipOut
from app.services.campaigns import related_ids


def summarize(db: Session, ad: Advertisement) -> AdvertisementSummary:
    preview = (ad.text or "").strip().replace("\n", " ")
    if len(preview) > 220:
        preview = preview[:217] + "..."
    return AdvertisementSummary(
        id=ad.id,
        is_seed=ad.is_seed,
        text=preview or "(image or URL submission without text)",
        source=ad.source,
        source_url=ad.source_url,
        analysis_status=ad.analysis_status,
        review_status=ad.review_status,
        risk_score=ad.risk_score,
        risk_category=ad.risk_category,
        created_at=ad.created_at,
        entity_count=len(ad.entities),
        related_count=len(related_ids(db, ad.id)),
    )


def relationships_for(db: Session, ad_id: str) -> list[RelationshipOut]:
    rels = (
        db.query(AdvertisementRelationship)
        .filter(
            (AdvertisementRelationship.source_ad_id == ad_id)
            | (AdvertisementRelationship.target_ad_id == ad_id)
        )
        .all()
    )
    return [RelationshipOut.model_validate(rel) for rel in rels]


def detail(db: Session, ad: Advertisement) -> AdvertisementDetail:
    from app.services.anomalies import detect_content_anomalies
    from app.services.extraction import ExtractedItem
    from app.services.risk import SignalResult

    base = summarize(db, ad)
    base_data = base.model_dump()
    base_data.pop("text", None)  # detail overrides with full text; summary carries a truncated preview

    text = "\n".join(filter(None, [ad.text, ad.ocr_text, ad.source_url])).strip()
    entity_items = [
        ExtractedItem(
            entity_type=e.entity_type,
            raw_value=e.raw_value,
            normalized_value=e.normalized_value,
            source_text=e.source_text,
            extraction_method=e.extraction_method,
            confidence=e.confidence,
        )
        for e in ad.entities
    ]
    signal_items = [
        SignalResult(
            signal_type=s.signal_type,
            title=s.title,
            explanation=s.explanation,
            evidence=s.evidence,
            contribution=s.contribution,
            recommendation=getattr(s, "recommendation", "") or "",
        )
        for s in ad.signals
    ]
    detected_anomalies = detect_content_anomalies(text, entity_items, signal_items)

    missing_warnings: list[str] = []
    if not (ad.text or "").strip() and not (ad.ocr_text or "").strip():
        missing_warnings.append("No readable advertisement text was provided or extracted. Triage assessment cannot score risk without copy.")
    if ad.ocr_status in {"empty", "failed", "unavailable"}:
        missing_warnings.append(f"OCR status is '{ad.ocr_status}'. Image text could not be transcribed.")

    return AdvertisementDetail(
        **base_data,
        text=ad.text,
        image_filename=ad.image_filename,
        ocr_text=ad.ocr_text,
        ocr_status=ad.ocr_status,
        limitations=ad.limitations,
        recommendation=ad.recommendation,
        analyzed_at=ad.analyzed_at,
        missing_data_warnings=missing_warnings,
        entities=ad.entities,
        signals=ad.signals,
        anomalies=[
            {
                "id": a.id,
                "anomaly_type": a.anomaly_type,
                "title": a.title,
                "explanation": a.explanation,
                "evidence": a.evidence,
                "severity": a.severity,
            }
            for a in detected_anomalies
        ],
        notes=ad.notes,
        relationships=relationships_for(db, ad.id),
    )
