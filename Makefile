.PHONY: install test benchmark demo serve examples docker-build clean

install:
	pip install -e ".[dev]"

test:
	pytest -v --durations=10

benchmark:
	pactum benchmark -n 2000

demo:
	pactum demo

serve:
	pactum serve --host 0.0.0.0 --port 8000

examples:
	python examples/01_basic_two_service_barter.py
	python examples/02_cross_api_rate_limit_rebalancing.py
	python examples/03_gpu_vram_for_priority_queue_swap.py
	python examples/04_dynamic_equilibrium_market.py

docker-build:
	docker build -t pactum-kernel:latest .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache dist build .coverage
