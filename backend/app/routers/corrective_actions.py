import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.entities import CorrectiveAction, Incident, AuditLog
from backend.app.schemas.schemas import CorrectiveActionResponse, CorrectiveActionUpdate, PaginatedResponse

router = APIRouter(prefix="/corrective-actions", tags=["Corrective Actions"])

@router.get("", response_model=PaginatedResponse[CorrectiveActionResponse])
def get_corrective_actions(
    incident_id: Optional[str] = Query(None, description="Filter by parent incident"),
    action_status: Optional[str] = Query(None, description="Filter by action status"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(CorrectiveAction)
    if incident_id:
        query = query.filter(CorrectiveAction.incident_id == incident_id)
    if action_status:
        query = query.filter(CorrectiveAction.action_status == action_status)
    if verification_status:
        query = query.filter(CorrectiveAction.verification_status == verification_status)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    actions = query.order_by(desc(CorrectiveAction.created_at)).offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=[CorrectiveActionResponse.model_validate(a) for a in actions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.patch("/{action_id}", response_model=CorrectiveActionResponse)
def update_corrective_action(
    action_id: str,
    update_data: CorrectiveActionUpdate,
    db: Session = Depends(get_db)
):
    action = db.query(CorrectiveAction).filter(CorrectiveAction.corrective_action_id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Corrective action '{action_id}' not found")

    old_state = {
        "action_status": action.action_status,
        "verification_status": action.verification_status,
        "completed_at": action.completed_at.isoformat() if action.completed_at else None,
        "verified_at": action.verified_at.isoformat() if action.verified_at else None,
    }

    # BUSINESS RULE 8 VALIDATION GATE:
    # Cannot set action_status = 'CLOSED' without verification_status == 'VERIFIED' and non-null verified_at!
    target_action_status = update_data.action_status or action.action_status
    target_verification_status = update_data.verification_status or action.verification_status

    if target_action_status == "CLOSED":
        if target_verification_status != "VERIFIED" and action.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=422,
                detail="Verification Gate Rejection: Corrective action cannot transition to CLOSED without verified_at and verification_status = 'VERIFIED'."
            )

    now = datetime.utcnow()

    # Lifecycle state updates
    if update_data.action_status:
        if update_data.action_status == "IN_PROGRESS" and not action.started_at:
            action.started_at = now
        elif update_data.action_status == "COMPLETED" and not action.completed_at:
            action.completed_at = now
        action.action_status = update_data.action_status

    if update_data.verification_status:
        if update_data.verification_status == "VERIFIED":
            action.verified_at = now
        action.verification_status = update_data.verification_status

    # Record Audit Log
    changes = {
        "before": old_state,
        "after": {
            "action_status": action.action_status,
            "verification_status": action.verification_status,
            "completed_at": action.completed_at.isoformat() if action.completed_at else None,
            "verified_at": action.verified_at.isoformat() if action.verified_at else None,
        },
        "notes": update_data.notes
    }
    audit = AuditLog(
        entity_type="corrective_actions",
        entity_id=action.corrective_action_id,
        action="STATUS_UPDATE",
        actor=update_data.actor,
        changes_json=json.dumps(changes),
        timestamp=now
    )
    db.add(audit)
    db.commit()
    db.refresh(action)

    return CorrectiveActionResponse.model_validate(action)

@router.post("/{action_id}/verify", response_model=CorrectiveActionResponse)
def verify_corrective_action(
    action_id: str,
    actor: str = Query("SAFETY_INSPECTOR", description="Auditor performing sign-off"),
    notes: Optional[str] = Query(None, description="Verification notes"),
    db: Session = Depends(get_db)
):
    action = db.query(CorrectiveAction).filter(CorrectiveAction.corrective_action_id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Corrective action '{action_id}' not found")

    if not action.completed_at:
        action.completed_at = datetime.utcnow()

    action.verified_at = datetime.utcnow()
    action.verification_status = "VERIFIED"
    action.action_status = "CLOSED"
    action.issue_type = None  # Clears unverified anomaly flag

    audit = AuditLog(
        entity_type="corrective_actions",
        entity_id=action.corrective_action_id,
        action="SAFETY_VERIFIED_SIGN_OFF",
        actor=actor,
        changes_json=json.dumps({"verified_at": action.verified_at.isoformat(), "notes": notes}),
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(action)

    return CorrectiveActionResponse.model_validate(action)
