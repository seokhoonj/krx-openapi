# Run the standard CI checks (test, lint, types) locally. Dev extras: uv pip install -e ".[dev]"
.PHONY: check test lint types

check: test lint types

test:
	pytest -q

lint:
	ruff check src tests

types:
	mypy
