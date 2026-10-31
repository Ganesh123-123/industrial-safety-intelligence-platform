import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from backend.app.database import SessionLocal
from backend.app.services.validation import DataValidationService

def main():
    print("============================================================")
    print("Executing 18-Point Industrial Safety Data Validation Framework")
    print("============================================================")
    
    db = SessionLocal()
    try:
        service = DataValidationService(db)
        report = service.run_all_checks()
        
        print(f"\nValidation Summary: {report.passed_checks}/{report.total_checks} PASSED | {report.failed_checks} FAILED\n")
        
        md_lines = [
            "# Industrial Safety Intelligence Platform - Data Validation Report",
            "",
            f"**Execution Timestamp**: {report.generated_at.isoformat()} UTC",
            f"**Total Checks Run**: {report.total_checks}",
            f"**Passed**: {report.passed_checks} | **Failed / Exceptions Detected**: {report.failed_checks}",
            "",
            "> [!NOTE]",
            "> In anomaly evaluation mode, checks corresponding to controlled anomaly fixtures (e.g. pre-alarm acknowledgements, impossible interlock states, missing incident contexts, replays, unverified closures) flag intentional synthetic fixture exceptions.",
            "",
            "## Check Results Breakdown",
            "",
            "| # | Check Name | Status | Records Evaluated | Failure / Anomaly Count | Explanation |",
            "|---|---|---|---|---|---|"
        ]

        for idx, check in enumerate(report.checks, 1):
            status_icon = "PASS" if check.status == "PASSED" else "ANOMALY_DETECTED"
            print(f"[{status_icon}] {check.check_name}: {check.records_checked} checked, {check.failure_count} exceptions.")
            if check.failure_count > 0:
                print(f"      Example IDs: {', '.join(check.example_affected_ids[:4])}")
                
            md_lines.append(
                f"| {idx} | **{check.check_name}** | `{check.status}` | {check.records_checked} | {check.failure_count} | {check.explanation} |"
            )

        md_lines.append("")
        md_lines.append("## Detailed Investigation Guidance")
        md_lines.append("")
        for idx, check in enumerate(report.checks, 1):
            if check.failure_count > 0:
                md_lines.append(f"### {idx}. {check.check_name}")
                md_lines.append(f"- **Status**: `{check.status}`")
                md_lines.append(f"- **Affected Count**: {check.failure_count}")
                md_lines.append(f"- **Sample IDs**: `{', '.join(check.example_affected_ids)}`")
                md_lines.append(f"- **Investigation Protocol**: {check.suggested_investigation}")
                md_lines.append("")

        # Save to docs/VALIDATION_REPORT.md
        report_path = root_dir / "docs" / "VALIDATION_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"\nDetailed markdown validation report written to '{report_path}'.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
