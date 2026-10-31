import csv
import io
import json
from typing import Generator, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.entities import (
    Plant, Machine, SafetyZone, Interlock, AlarmDefinition,
    AlarmEvent, Acknowledgement, Incident, CorrectiveAction
)

ENTITY_MODEL_MAP = {
    "plants": Plant,
    "machines": Machine,
    "safety-zones": SafetyZone,
    "interlocks": Interlock,
    "alarm-definitions": AlarmDefinition,
    "alarms": AlarmEvent,
    "acknowledgements": Acknowledgement,
    "incidents": Incident,
    "corrective-actions": CorrectiveAction
}

class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_entity_csv(self, entity_name: str) -> str:
        model = ENTITY_MODEL_MAP.get(entity_name)
        if not model:
            raise ValueError(f"Unknown entity '{entity_name}'. Supported: {list(ENTITY_MODEL_MAP.keys())}")

        output = io.StringIO()
        columns = [c.name for c in model.__table__.columns]
        writer = csv.writer(output)
        writer.writerow(columns)

        # Stream rows in chunks
        chunk_size = 1000
        offset = 0
        while True:
            rows = self.db.query(model).offset(offset).limit(chunk_size).all()
            if not rows:
                break
            for r in rows:
                writer.writerow([getattr(r, col, "") for col in columns])
            offset += chunk_size

        return output.getvalue()

    def export_entity_json(self, entity_name: str) -> List[Dict[str, Any]]:
        model = ENTITY_MODEL_MAP.get(entity_name)
        if not model:
            raise ValueError(f"Unknown entity '{entity_name}'. Supported: {list(ENTITY_MODEL_MAP.keys())}")

        columns = [c.name for c in model.__table__.columns]
        rows = self.db.query(model).limit(5000).all()
        results = []
        for r in rows:
            item = {}
            for col in columns:
                val = getattr(r, col)
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                item[col] = val
            results.append(item)
        return results

    def get_manifest(self) -> Dict[str, Any]:
        manifest_path = settings.GENERATED_DATA_DIR / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "origin": "Synthetic",
            "message": "No data generation run has been executed yet."
        }
