.PHONY: test test-unit test-integration test-e2e test-live test-cov test-cov-all test-watch install-dev clean run

# Install development dependencies (uses uv)
install-dev:
	uv pip install -e ".[all]"
	uv pip install -r requirements-dev.txt

# Run Feishu bot (uses uv)
run:
	SSL_CERT_FILE=/private/etc/ssl/cert.pem uv run nura run --config examples/feishu_bot/config.json --platform feishu

# Run all tests (unit + integration, exclude e2e and live)
test:
	uv run pytest tests/unit tests/integration -v

# Run only unit tests (fast)
test-unit:
	uv run pytest tests/unit -v -m unit

# Run integration tests
test-integration:
	uv run pytest tests/integration -v -m integration

# Run E2E tests
test-e2e:
	uv run pytest tests/e2e -v -m e2e

# Run live tests (require real credentials)
test-live:
	NURA_LIVE_TEST=1 uv run pytest tests -v -m live

# Run with coverage
test-cov:
	uv run pytest tests/unit tests/integration -v --cov=nura --cov-config=.coveragerc --cov-report=html --cov-report=term

# Run with full coverage (unit + integration + live tests)
test-cov-all:
	@echo "Running unit + integration tests with coverage..."
	uv run pytest tests/unit tests/integration -v --cov=nura --cov-config=.coveragerc --cov-report=term
	@echo ""
	@echo "Running live tests with coverage..."
	NURA_LIVE_TEST=1 uv run pytest tests -v -m live --cov=nura --cov-config=.coveragerc --cov-append --cov-report=term

# Watch mode
test-watch:
	uv run pytest-watch tests/unit

# Parallel execution
test-parallel:
	uv run pytest tests/unit tests/integration -n auto

# Clean build artifacts and old logs (logs older than 7 days)
clean:
	rm -rf build/ dist/ htmlcov/ .mypy_cache/ .pytest_cache/ .ruff_cache/
	rm -f *.egg-info .coverage coverage.json coverage_output.txt output.mp3
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@if [ -d logs/ ]; then \
		echo "Cleaning logs older than 7 days..."; \
		find logs/ -type f -mtime +7 -delete; \
		find logs/ -type d -empty -delete; \
	fi
