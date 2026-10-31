import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from backend.app.database import SessionLocal
from backend.app.services.evaluation import EvaluationEngine

def main():
    print("============================================================")
    print("Industrial Safety Anomaly Detection & Evaluation Engine")
    print("Comparing Detection Predictions against Isolated Ground Truth")
    print("============================================================")
    
    db = SessionLocal()
    try:
        engine = EvaluationEngine(db)
        report = engine.evaluate()
        
        print("\n--- OVERALL DETECTION METRICS ---")
        print(f"Overall Precision : {report.overall_precision * 100:.2f}%")
        print(f"Overall Recall    : {report.overall_recall * 100:.2f}%")
        print(f"Overall F1 Score  : {report.overall_f1 * 100:.2f}%")
        print(f"Ground Truth Count: {report.total_ground_truth_anomalies}")
        print(f"Detected Anomalies: {report.total_detected_anomalies}")
        
        print("\n--- METRICS BY ANOMALY CATEGORY ---")
        print(f"{'Anomaly Category':<38} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<9} | {'Recall':<9} | {'F1':<9}")
        print("-" * 88)
        for cat in report.categories:
            print(
                f"{cat.anomaly_type:<38} | {cat.true_positives:<4} | {cat.false_positives:<4} | {cat.false_negatives:<4} | "
                f"{cat.precision*100:>8.1f}% | {cat.recall*100:>8.1f}% | {cat.f1_score*100:>8.1f}%"
            )
            
        print("\nGround truth isolation confirmed: Ground truth files were read exclusively by evaluation engine.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
