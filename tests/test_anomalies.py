import pytest
from backend.app.database import SessionLocal
from backend.app.services.evaluation import EvaluationEngine

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

def test_evaluation_engine_metrics(db_session):
    eval_engine = EvaluationEngine(db_session)
    report = eval_engine.evaluate()
    
    assert report.total_ground_truth_anomalies == 24
    assert report.overall_precision == 1.0
    assert report.overall_recall == 1.0
    assert report.overall_f1 == 1.0

    categories = {c.anomaly_type: c for c in report.categories}
    expected_categories = [
        "ACKNOWLEDGEMENT_BEFORE_ALARM",
        "IMPOSSIBLE_INTERLOCK_STATE",
        "INCIDENT_MISSING_TRIGGER_CONTEXT",
        "DUPLICATE_ALARM_REPLAY",
        "ACTION_CLOSED_WITHOUT_VERIFICATION"
    ]

    for ec in expected_categories:
        assert ec in categories
        cat_metric = categories[ec]
        assert cat_metric.true_positives > 0
        assert cat_metric.false_positives == 0
        assert cat_metric.false_negatives == 0
        assert cat_metric.precision == 1.0
        assert cat_metric.recall == 1.0
        assert cat_metric.f1_score == 1.0
