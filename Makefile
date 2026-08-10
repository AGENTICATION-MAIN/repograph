.PHONY: install test benchmark scan sample clean docker-build

install:
	pip install -e ".[dev]"

test:
	pytest -v --durations=10

benchmark:
	pytest tests/benchmarks/ -v -s

scan:
	repograph scan .

sample:
	repograph scan ./tests/fixtures/sample_repo

docker-build:
	docker build -t repograph:latest .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache dist build .coverage
