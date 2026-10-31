from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.validation import DataValidationService
from backend.app.schemas.schemas import ValidationReport

router = APIRouter(prefix="", tags=["Data Quality & Validation"])

@router.get("/data-quality", response_model=ValidationReport)
def get_data_quality_report(db: Session = Depends(get_db)):
    val_service = DataValidationService(db)
    return val_service.run_all_checks()

@router.post("/validate", response_model=ValidationReport)
def run_validation(db: Session = Depends(get_db)):
    val_service = DataValidationService(db)
    return val_service.run_all_checks()
