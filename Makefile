.PHONY: install test lint format benchmark demo serve clean docker-build

install:
	pip install -e ".[dev]"

test:
	pytest -v --durations=10

benchmark:
	pytest tests/benchmarks/ -s

demo:
	python -m aegis demo

serve:
	python -m aegis serve --host 0.0.0.0 --port 8000

examples:
	python examples/01_quickstart.py
	python examples/02_financial_agent_guard.py
	python examples/03_prompt_injection_defense.py
	python examples/04_merkle_audit_verification.py

docker-build:
	docker build -t aegis-kernel:latest .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache dist build .coverage
