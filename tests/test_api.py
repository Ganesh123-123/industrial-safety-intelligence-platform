import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["database"] == "HEALTHY"

def test_overview_endpoint():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_plants"] == 4
    assert data["total_machines"] >= 12
    assert data["total_alarms"] >= 2000
    assert len(data["alarms_trend"]) > 0

def test_plants_and_machines_endpoints():
    p_resp = client.get("/api/plants")
    assert p_resp.status_code == 200
    plants = p_resp.json()
    assert len(plants) == 4

    m_resp = client.get("/api/machines?page=1&page_size=10")
    assert m_resp.status_code == 200
    m_data = m_resp.json()
    assert len(m_data["items"]) == 10
    assert m_data["total"] >= 12

def test_alarms_pagination_and_filters():
    resp = client.get("/api/alarms?severity=CRITICAL&page=1&page_size=15")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["severity"] == "CRITICAL"

def test_anomalies_endpoint():
    resp = client.get("/api/anomalies")
    assert resp.status_code == 200
    anomalies = resp.json()
    assert len(anomalies) >= 24
    types = {a["anomaly_type"] for a in anomalies}
    assert "ACKNOWLEDGEMENT_BEFORE_ALARM" in types
    assert "IMPOSSIBLE_INTERLOCK_STATE" in types
    assert "ACTION_CLOSED_WITHOUT_VERIFICATION" in types

def test_corrective_action_verification_gate():
    # Attempt to close an unverified action without verification should return 422
    actions_resp = client.get("/api/corrective-actions?verification_status=PENDING")
    assert actions_resp.status_code == 200
    actions = actions_resp.json()["items"]
    assert len(actions) > 0
    target_id = actions[0]["corrective_action_id"]

    # Try to close without verifying
    patch_resp = client.patch(
        f"/api/corrective-actions/{target_id}",
        json={"action_status": "CLOSED", "actor": "TEST_OPERATOR"}
    )
    assert patch_resp.status_code == 422
    assert "Verification Gate Rejection" in patch_resp.json()["detail"]

def test_evaluation_metrics_endpoint():
    resp = client.get("/api/metrics/evaluation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_precision"] == 1.0
    assert data["overall_recall"] == 1.0

def test_export_endpoints():
    csv_resp = client.get("/api/export/plants?format=csv")
    assert csv_resp.status_code == 200
    assert "plant_id" in csv_resp.text

    json_resp = client.get("/api/export/plants?format=json")
    assert json_resp.status_code == 200
    assert isinstance(json_resp.json(), list)

    manifest_resp = client.get("/api/export/manifest")
    assert manifest_resp.status_code == 200
    assert manifest_resp.json()["seed"] == 20261022
