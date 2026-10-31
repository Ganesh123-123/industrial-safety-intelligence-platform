from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.entities import AlarmEvent, Acknowledgement, AlarmDefinition
from backend.app.services.rules import BusinessRulesEngine
from backend.app.services.evaluation import EvaluationEngine
from backend.app.schemas.schemas import EvaluationReport, RepeatedConditionScore

router = APIRouter(prefix="", tags=["Metrics & Analytics"])

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    rules_engine = BusinessRulesEngine(db)
    repeated_scores = rules_engine.calculate_repeated_condition_scores(window_hours=72)
    
    # SLA compliance
    total_acks = db.query(func.count(Acknowledgement.acknowledgement_id)).scalar() or 0
    delayed_acks = db.query(func.count(Acknowledgement.acknowledgement_id)).filter(
        Acknowledgement.acknowledgement_status == "DELAYED"
    ).scalar() or 0
    timely_acks = db.query(func.count(Acknowledgement.acknowledgement_id)).filter(
        Acknowledgement.acknowledgement_status == "TIMELY"
    ).scalar() or 0
    pre_alarm_acks = db.query(func.count(Acknowledgement.acknowledgement_id)).filter(
        Acknowledgement.response_seconds < 0
    ).scalar() or 0

    sla_compliance_rate = (timely_acks / total_acks * 100.0) if total_acks > 0 else 100.0

    return {
        "repeated_condition_scores": repeated_scores[:10],
        "sla_metrics": {
            "total_acknowledgements": total_acks,
            "timely_acknowledgements": timely_acks,
            "delayed_acknowledgements": delayed_acks,
            "pre_alarm_anomalous_acknowledgements": pre_alarm_acks,
            "compliance_percentage": round(sla_compliance_rate, 2)
        }
    }

@router.get("/metrics/evaluation", response_model=EvaluationReport)
def get_evaluation_metrics(db: Session = Depends(get_db)):
    eval_engine = EvaluationEngine(db)
    return eval_engine.evaluate()

@router.post("/analyze")
def trigger_analysis(db: Session = Depends(get_db)):
    rules_engine = BusinessRulesEngine(db)
    anomalies = rules_engine.detect_all()
    repeated = rules_engine.calculate_repeated_condition_scores(window_hours=72)
    return {
        "status": "COMPLETED",
        "total_anomalies_detected": len(anomalies),
        "repeated_condition_candidates": len(repeated),
        "top_hazard_machine": repeated[0].machine_code if repeated else "NONE"
    }
