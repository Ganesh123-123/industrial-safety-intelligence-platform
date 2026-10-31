from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.entities import DataGenerationRun
from backend.app.services.generator import SyntheticDataGenerator
from backend.app.schemas.schemas import DataGenerationRequest

router = APIRouter(prefix="", tags=["Data Generation"])

@router.get("/generation-runs")
def get_generation_runs(db: Session = Depends(get_db)):
    runs = db.query(DataGenerationRun).order_by(desc(DataGenerationRun.generated_at)).limit(20).all()
    return [
        {
            "run_id": r.run_id,
            "seed": r.seed,
            "profile": r.profile,
            "generated_at": r.generated_at.isoformat(),
            "canonical_checksum": r.canonical_checksum
        } for r in runs
    ]

@router.post("/generate-data")
def generate_data(request: DataGenerationRequest, db: Session = Depends(get_db)):
    try:
        generator = SyntheticDataGenerator(
            seed=request.seed,
            profile=request.profile,
            event_count=request.event_count
        )
        result = generator.run(db=db, export_files=True)
        return {
            "status": "SUCCESS",
            "message": f"Successfully generated {result['summary']['alarm_events']} alarm events using profile '{request.profile}'.",
            "seed": request.seed,
            "profile": request.profile,
            "canonical_checksum": result["canonical_checksum"],
            "summary": result["summary"],
            "ground_truth_count": result["ground_truth_count"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
