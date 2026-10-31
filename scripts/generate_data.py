import argparse
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from backend.app.database import SessionLocal
from backend.app.services.generator import SyntheticDataGenerator

def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator for Industrial Safety Platform")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed (default: 20261022)")
    parser.add_argument("--profile", type=str, choices=["starter", "full"], default="starter", help="Dataset size profile ('starter' or 'full')")
    parser.add_argument("--events", type=int, default=None, help="Override target event count")
    parser.add_argument("--no-db", action="store_true", help="Do not persist to database, only export CSV/JSON")
    
    args = parser.parse_args()
    
    print(f"============================================================")
    print(f"Starting Industrial Safety Synthetic Data Generation")
    print(f"Profile: {args.profile} | Seed: {args.seed} | Target Events: {args.events or 'Profile Default'}")
    print(f"============================================================")
    
    generator = SyntheticDataGenerator(
        seed=args.seed,
        profile=args.profile,
        event_count=args.events
    )
    
    db = None if args.no_db else SessionLocal()
    try:
        results = generator.run(db=db, export_files=True)
        print("\n--- GENERATION COMPLETE ---")
        print(f"Canonical Checksum: {results['canonical_checksum']}")
        print(f"Ground Truth Anomalies Injected: {results['ground_truth_count']}")
        print("\nEntity Counts:")
        for entity, count in results["summary"].items():
            print(f"  - {entity.ljust(30)}: {count}")
        print("\nFiles written to 'data/generated/' and 'data/evaluation/'.")
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    main()
