from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.rules import BusinessRulesEngine
from backend.app.schemas.schemas import AnomalyItem

router = APIRouter(prefix="/anomalies", tags=["Anomaly Center"])

@router.get("", response_model=List[AnomalyItem])
def get_anomalies(
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type code"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    db: Session = Depends(get_db)
):
    rules_engine = BusinessRulesEngine(db)
    anomalies = rules_engine.detect_all()

    if anomaly_type:
        anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]
    if severity:
        anomalies = [a for a in anomalies if a.severity == severity]

    return anomalies

@router.get("/{anomaly_id}", response_model=AnomalyItem)
def get_anomaly_detail(anomaly_id: str, db: Session = Depends(get_db)):
    rules_engine = BusinessRulesEngine(db)
    anomalies = rules_engine.detect_all()
    
    for a in anomalies:
        if a.anomaly_id == anomaly_id:
            return a
            
    raise HTTPException(status_code=404, detail=f"Anomaly item '{anomaly_id}' not found")
