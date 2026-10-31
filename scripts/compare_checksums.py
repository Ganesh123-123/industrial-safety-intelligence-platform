import sys
import argparse
import shutil
import tempfile
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from backend.app.services.generator import SyntheticDataGenerator

def main():
    parser = argparse.ArgumentParser(description="Industrial Safety Platform - Reproducibility & Checksum Audit")
    parser.add_argument("--profile", type=str, default="starter", choices=["starter", "full"], help="Profile to audit ('starter' or 'full')")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed (default: 20261022)")
    args = parser.parse_args()
    
    seed = args.seed
    profile = args.profile
    
    print("============================================================")
    print("Industrial Safety Platform - Reproducibility & Checksum Audit")
    print(f"Comparing two independent runs with Seed: {seed}, Profile: {profile}")
    print("============================================================")

    # Run 1
    print("\nExecuting Generation Run 1...")
    gen1 = SyntheticDataGenerator(seed=seed, profile=profile)
    res1 = gen1.run(db=None, export_files=False)
    hash1 = res1["canonical_checksum"]
    summary1 = res1["summary"]
    gt1 = res1["ground_truth_count"]
    print(f"Run 1 Canonical Hash: {hash1}")

    # Run 2
    print("Executing Generation Run 2...")
    gen2 = SyntheticDataGenerator(seed=seed, profile=profile)
    res2 = gen2.run(db=None, export_files=False)
    hash2 = res2["canonical_checksum"]
    summary2 = res2["summary"]
    gt2 = res2["ground_truth_count"]
    print(f"Run 2 Canonical Hash: {hash2}")

    print("\n--- COMPARISON RESULTS ---")
    mismatches = []
    
    if hash1 != hash2:
        mismatches.append(f"Canonical Checksum Mismatch! {hash1} vs {hash2}")
    else:
        print("[PASS] Canonical SHA-256 Checksum: IDENTICAL")

    if gt1 != gt2:
        mismatches.append(f"Ground Truth Fixture Count Mismatch! {gt1} vs {gt2}")
    else:
        print(f"[PASS] Ground Truth Fixtures Count: IDENTICAL ({gt1} fixtures)")

    # Compare entity row counts
    all_keys = set(summary1.keys()).union(set(summary2.keys()))
    row_count_match = True
    for k in sorted(all_keys):
        c1 = summary1.get(k, 0)
        c2 = summary2.get(k, 0)
        if c1 != c2:
            row_count_match = False
            mismatches.append(f"Row count mismatch for {k}: {c1} vs {c2}")
    if row_count_match:
        print(f"[PASS] All {len(all_keys)} Entity Row Counts: 100% IDENTICAL")

    # Sample check primary keys
    pk_sample_match = (
        [p.plant_id for p in gen1.plants] == [p.plant_id for p in gen2.plants] and
        [m.machine_id for m in gen1.machines] == [m.machine_id for m in gen2.machines] and
        [e.alarm_event_id for e in gen1.alarm_events[:100]] == [e.alarm_event_id for e in gen2.alarm_events[:100]]
    )
    if pk_sample_match:
        print("[PASS] Primary Key Ordering & Deterministic IDs: 100% IDENTICAL")
    else:
        mismatches.append("Primary key sequence mismatch between runs")

    if mismatches:
        print("\n[FAIL] REPRODUCIBILITY AUDIT FAILED:")
        for m in mismatches:
            print(f"  - {m}")
        sys.exit(1)
    else:
        print("\n============================================================")
        print("REPRODUCIBILITY AUDIT PASSED: 100% DETERMINISTIC VERIFICATION")
        print("============================================================")

if __name__ == "__main__":
    main()
