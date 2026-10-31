import pytest
from backend.app.database import SessionLocal
from backend.app.services.rules import BusinessRulesEngine
from backend.app.models.entities import AlarmEvent, AlarmDefinition

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

def test_repeated_condition_score_calculation(db_session):
    engine = BusinessRulesEngine(db_session)
    scores = engine.calculate_repeated_condition_scores(window_hours=72)
    assert isinstance(scores, list)
    assert len(scores) > 0
    
    # Check top score structure and bounds
    top = scores[0]
    assert 0.0 <= top.score <= 100.0
    assert top.level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(top.explanation) > 0
    assert "computed score" in top.explanation

def test_severity_priority_scoring(db_session):
    engine = BusinessRulesEngine(db_session)
    
    crit_def = db_session.query(AlarmDefinition).filter(AlarmDefinition.severity == "CRITICAL").first()
    alarm = db_session.query(AlarmEvent).filter(AlarmEvent.machine_state == "EMERGENCY_STOP").first()
    
    if crit_def and alarm:
        priority = engine.calculate_alarm_priority(alarm, crit_def)
        assert priority["priority_score"] >= 1000
        assert priority["triage_urgency"] in ["IMMEDIATE", "ELEVATED"]

def test_delayed_acknowledgement_detection(db_session):
    engine = BusinessRulesEngine(db_session)
    anomalies = engine.detect_acknowledgement_anomalies()
    assert len(anomalies) >= 5
    for a in anomalies:
        assert a.anomaly_type == "ACKNOWLEDGEMENT_BEFORE_ALARM"
        assert a.evidence["response_seconds"] < 0
        assert "strictly precedes" in a.explanation

def test_impossible_interlock_detection(db_session):
    engine = BusinessRulesEngine(db_session)
    anomalies = engine.detect_impossible_interlock_states()
    assert len(anomalies) >= 5
    for a in anomalies:
        assert a.anomaly_type == "IMPOSSIBLE_INTERLOCK_STATE"
        assert a.severity == "CRITICAL"
        assert a.evidence["machine_state"] == "RUNNING"
        assert a.evidence["interlock_state_snapshot"] in ["TRIPPED", "OPEN"]

def test_unverified_action_detection(db_session):
    engine = BusinessRulesEngine(db_session)
    anomalies = engine.detect_unverified_closed_actions()
    assert len(anomalies) >= 4
    for a in anomalies:
        assert a.anomaly_type == "ACTION_CLOSED_WITHOUT_VERIFICATION"
        assert a.evidence["action_status"] == "CLOSED"
        assert a.evidence["verification_status"] != "VERIFIED" or a.evidence["verified_at"] is None
