.PHONY: setup check test lint format clean

PYTHON  := python
PIP     := $(PYTHON) -m pip
PYTEST  := $(PYTHON) -m pytest
RUFF    := $(PYTHON) -m ruff
MYPY    := $(PYTHON) -m mypy
LINT    := lint-imports

# ── Bootstrap ────────────────────────────────────────────────────────────────
setup:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	pre-commit install

# ── All checks (mirrors check.ps1) ──────────────────────────────────────────
check: format lint test

# ── Formatting ───────────────────────────────────────────────────────────────
format:
	$(RUFF) format .
	$(RUFF) check --fix .

# ── Linting ──────────────────────────────────────────────────────────────────
lint:
	$(RUFF) check .
	$(MYPY) libs/
	$(LINT)

# ── Tests ────────────────────────────────────────────────────────────────────
test:
	$(PYTEST) tests/unit tests/leakage --cov=libs --cov-report=term-missing

test-all:
	$(PYTEST) tests/ --cov=. --cov-report=term-missing

test-leakage:
	$(PYTEST) tests/leakage -v

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info"    -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"         -delete 2>/dev/null || true

