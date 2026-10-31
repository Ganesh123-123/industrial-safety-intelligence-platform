import csv
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["Exports"])

@router.get("/manifest")
def get_manifest(db: Session = Depends(get_db)):
    svc = ExportService(db)
    return svc.get_manifest()

@router.get("/evaluation/ground-truth")
def get_evaluation_ground_truth(
    format: str = Query("csv", description="Export format: 'csv' or 'json'")
):
    if format.lower() == "json":
        path = settings.EVALUATION_DATA_DIR / "ground_truth.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Ground truth JSON not found. Run data generation first.")
        return FileResponse(path, media_type="application/json", filename="ground_truth_EVALUATION_ONLY.json")
    else:
        path = settings.EVALUATION_DATA_DIR / "ground_truth.csv"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Ground truth CSV not found. Run data generation first.")
        return FileResponse(path, media_type="text/csv", filename="ground_truth_EVALUATION_ONLY.csv")

@router.get("/{entity}")
def export_entity(
    entity: str,
    format: str = Query("csv", description="Format: 'csv' or 'json'"),
    db: Session = Depends(get_db)
):
    svc = ExportService(db)
    try:
        if format.lower() == "json":
            data = svc.export_entity_json(entity)
            return JSONResponse(content=data)
        else:
            csv_content = svc.export_entity_csv(entity)
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={entity}.csv"}
            )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
