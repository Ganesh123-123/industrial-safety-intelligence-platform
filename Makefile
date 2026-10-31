.PHONY: help setup generate-starter generate-full validate evaluate compare-checksums test run-backend run-frontend

help:
	@echo "Industrial Safety Intelligence Platform - Commands:"
	@echo "  make setup              - Install backend and frontend dependencies"
	@echo "  make generate-starter   - Generate deterministic starter dataset"
	@echo "  make generate-full      - Generate full 50,000 alarm event dataset"
	@echo "  make validate           - Run 18-point data validation framework"
	@echo "  make evaluate           - Evaluate anomaly detection vs isolated ground truth"
	@echo "  make compare-checksums  - Verify deterministic reproducibility across runs"
	@echo "  make test               - Run automated pytest test suite"
	@echo "  make run-backend        - Start FastAPI backend server on port 8000"
	@echo "  make run-frontend       - Start Vite React frontend on port 5173"

setup:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install

generate-starter:
	python scripts/generate_data.py --profile starter

generate-full:
	python scripts/generate_data.py --profile full

validate:
	python scripts/validate_data.py

evaluate:
	python scripts/evaluate_detection.py

compare-checksums:
	python scripts/compare_checksums.py

test:
	python -m pytest -v

run-backend:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev
