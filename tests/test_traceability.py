import pytest
from backend.app.database import SessionLocal
from backend.app.models.entities import Incident
from backend.app.services.traceability import TraceabilityService

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

def test_traceability_graph_construction(db_session):
    service = TraceabilityService(db_session)
    # Pick normal incident with triggering alarm
    inc = db_session.query(Incident).filter(Incident.triggering_alarm_event_id.isnot(None)).first()
    assert inc is not None

    trace = service.build_incident_traceability(inc.incident_id)
    assert trace is not None
    assert trace.incident.incident_id == inc.incident_id
    assert len(trace.timeline) >= 4

    node_types = {n.node_type for n in trace.timeline}
    assert "FACILITY_CONTEXT" in node_types
    assert "INCIDENT" in node_types
    assert "ALARM" in node_types

def test_traceability_gap_detection(db_session):
    service = TraceabilityService(db_session)
    # Pick fixture incident with missing trigger context
    inc = db_session.query(Incident).filter(Incident.triggering_alarm_event_id.is_(None)).first()
    assert inc is not None

    trace = service.build_incident_traceability(inc.incident_id)
    assert trace is not None
    assert trace.traceability_complete is False
    assert any("missing" in reason.lower() for reason in trace.missing_evidence_reasons)
    
    # Check that an explicit gap node exists
    gap_nodes = [n for n in trace.timeline if n.is_gap]
    assert len(gap_nodes) > 0
    assert gap_nodes[0].node_type == "GAP_TRIGGER"
