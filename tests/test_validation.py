import pytest
from backend.app.database import SessionLocal
from backend.app.services.validation import DataValidationService

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

def test_validation_framework_execution(db_session):
    service = DataValidationService(db_session)
    report = service.run_all_checks()
    
    assert report.total_checks == 18
    assert report.passed_checks >= 13
    
    checks_by_name = {c.check_name: c for c in report.checks}
    
    # Critical integrity checks MUST pass 100%
    assert checks_by_name["1. Primary-Key Uniqueness"].status == "PASSED"
    assert checks_by_name["2. Foreign-Key Referential Integrity"].status == "PASSED"
    assert checks_by_name["3. Allowed Enum Values"].status == "PASSED"
    assert checks_by_name["4. Required Fields Non-Null"].status == "PASSED"
    assert checks_by_name["5. Machine-to-Plant Consistency"].status == "PASSED"
    assert checks_by_name["7. Alarm-Definition Compatibility"].status == "PASSED"
    assert checks_by_name["9. Event Occurrence vs Ingestion Timestamp"].status == "PASSED"
    assert checks_by_name["14. Derived Response-Time Reconciliation"].status == "PASSED"
    assert checks_by_name["15. Deterministic Identifier Formatting"].status == "PASSED"
    assert checks_by_name["17. Ground-Truth Data Isolation"].status == "PASSED"
    assert checks_by_name["18. Reproducible Generation Checksums"].status == "PASSED"
