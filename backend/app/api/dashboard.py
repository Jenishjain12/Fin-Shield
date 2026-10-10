from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Advertisement, AdvertisementRelationship, Alert
from app.schemas.common import AlertOut, DashboardSummary
from app.services.campaigns import list_campaigns
from app.services.serializers import summarize

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    total = db.query(func.count(Advertisement.id)).scalar() or 0
    seed_count = db.query(func.count(Advertisement.id)).filter(Advertisement.is_seed.is_(True)).scalar() or 0
    suspicious = (
        db.query(func.count(Advertisement.id)).filter(Advertisement.risk_score >= 25).scalar() or 0
    )
    high_risk = (
        db.query(func.count(Advertisement.id)).filter(Advertisement.risk_score >= 50).scalar() or 0
    )
    relationships = db.query(func.count(AdvertisementRelationship.id)).scalar() or 0
    distribution = {label: 0 for label in ("LOW", "MEDIUM", "HIGH", "CRITICAL")}
    for category, count in (
        db.query(Advertisement.risk_category, func.count(Advertisement.id)).group_by(Advertisement.risk_category).all()
    ):
        distribution[category] = count
    recent_ads = db.query(Advertisement).order_by(Advertisement.created_at.desc()).limit(8).all()
    recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(8).all()
    campaigns = list_campaigns(db)[:6]
    return DashboardSummary(
        total_advertisements=total,
        potentially_suspicious=suspicious,
        high_risk=high_risk,
        relationship_count=relationships,
        seed_advertisement_count=seed_count,
        risk_distribution=distribution,
        recent_advertisements=[summarize(db, ad) for ad in recent_ads],
        recent_alerts=[AlertOut.model_validate(alert) for alert in recent_alerts],
        campaign_activity=campaigns,
    )
