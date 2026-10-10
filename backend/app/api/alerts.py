from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Alert
from app.schemas.common import AlertOut, AlertUpdate

router = APIRouter()


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[AlertOut]:
    query = db.query(Alert)
    if unread_only:
        query = query.filter(Alert.is_read.is_(False))
    return [AlertOut.model_validate(alert) for alert in query.order_by(Alert.created_at.desc()).all()]


@router.patch("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: str, payload: AlertUpdate, db: Session = Depends(get_db)) -> AlertOut:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = payload.is_read
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)
