import csv
import json
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.rules import BusinessRulesEngine
from backend.app.schemas.schemas import EvaluationReport, EvaluationMetricCategory

CATEGORIES = [
    "ACKNOWLEDGEMENT_BEFORE_ALARM",
    "IMPOSSIBLE_INTERLOCK_STATE",
    "INCIDENT_MISSING_TRIGGER_CONTEXT",
    "DUPLICATE_ALARM_REPLAY",
    "ACTION_CLOSED_WITHOUT_VERIFICATION"
]

class EvaluationEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate(self) -> EvaluationReport:
        # Step 1: Run detection engine independently on the database
        rules_engine = BusinessRulesEngine(self.db)
        detected_anomalies = rules_engine.detect_all()
        
        # Build map of predictions: (anomaly_type, entity_id) -> detected item
        pred_map: Dict[tuple, Any] = {}
        for anom in detected_anomalies:
            pred_map[(anom.anomaly_type, anom.entity_id)] = anom

        # Step 2: Load ground truth (isolated file)
        gt_path = settings.EVALUATION_DATA_DIR / "ground_truth.csv"
        ground_truth: List[Dict[str, Any]] = []
        
        if gt_path.exists():
            with open(gt_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ground_truth.append(row)
        else:
            # Fallback to json if exists
            json_path = settings.EVALUATION_DATA_DIR / "ground_truth.json"
            if json_path.exists():
                with open(json_path, mode="r", encoding="utf-8") as f:
                    ground_truth = json.load(f)

        # Step 3: Compute TP, FP, FN per category
        category_metrics: List[EvaluationMetricCategory] = []
        
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        # Pre-group ground truth by category
        gt_by_cat: Dict[str, Dict[str, Dict[str, Any]]] = {c: {} for c in CATEGORIES}
        for item in ground_truth:
            cat = item.get("expected_anomaly_type")
            e_id = item.get("affected_entity_id")
            if cat in gt_by_cat:
                gt_by_cat[cat][e_id] = item

        for cat in CATEGORIES:
            cat_gt = gt_by_cat[cat]
            # Detected anomalies of this category
            cat_preds = {k[1]: v for k, v in pred_map.items() if k[0] == cat}
            
            tp = sum(1 for e_id in cat_preds if e_id in cat_gt)
            fp = sum(1 for e_id in cat_preds if e_id not in cat_gt)
            fn = sum(1 for e_id in cat_gt if e_id not in cat_preds)
            tn = 0  # In anomaly detection fixture evaluation, TN is large unflagged normal population
            
            total_tp += tp
            total_fp += fp
            total_fn += fn
            
            denom_p = tp + fp
            precision = (tp / denom_p) if denom_p > 0 else 0.0
            
            denom_r = tp + fn
            recall = (tp / denom_r) if denom_r > 0 else 0.0
            
            denom_f1 = precision + recall
            f1 = (2.0 * precision * recall / denom_f1) if denom_f1 > 0 else 0.0
            
            detection_rate = recall
            
            category_metrics.append(EvaluationMetricCategory(
                anomaly_type=cat,
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
                detection_rate=round(detection_rate, 4),
                total_ground_truth=len(cat_gt)
            ))

        # Overall metrics
        overall_p_denom = total_tp + total_fp
        overall_precision = (total_tp / overall_p_denom) if overall_p_denom > 0 else 0.0
        
        overall_r_denom = total_tp + total_fn
        overall_recall = (total_tp / overall_r_denom) if overall_r_denom > 0 else 0.0
        
        overall_f1_denom = overall_precision + overall_recall
        overall_f1 = (2.0 * overall_precision * overall_recall / overall_f1_denom) if overall_f1_denom > 0 else 0.0

        return EvaluationReport(
            overall_precision=round(overall_precision, 4),
            overall_recall=round(overall_recall, 4),
            overall_f1=round(overall_f1, 4),
            overall_detection_rate=round(overall_recall, 4),
            total_ground_truth_anomalies=len(ground_truth),
            total_detected_anomalies=len(detected_anomalies),
            categories=category_metrics,
            zero_division_policy="Returns 0.0 when denominator is zero"
        )
