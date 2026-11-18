"""Unit tests for Docker Compose and container packaging (Tier 6, task T6.4)."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INFRA_DIR = REPO_ROOT / "infra"


def test_dockerfiles_exist_and_valid():
    """Verify Dockerfile.api and Dockerfile.dashboard exist and contain required directives."""
    api_dockerfile = INFRA_DIR / "Dockerfile.api"
    dashboard_dockerfile = INFRA_DIR / "Dockerfile.dashboard"

    assert api_dockerfile.exists(), f"Missing {api_dockerfile}"
    assert dashboard_dockerfile.exists(), f"Missing {dashboard_dockerfile}"

    api_content = api_dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in api_content
    assert "EXPOSE 8000" in api_content
    assert "services.api.app:app" in api_content

    dash_content = dashboard_dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in dash_content
    assert "EXPOSE 8501" in dash_content
    assert "apps/dashboard/app.py" in dash_content


def test_docker_compose_structure():
    """Verify docker-compose.yml defines api, dashboard, and mlflow services with expected ports."""
    compose_file = INFRA_DIR / "docker-compose.yml"
    assert compose_file.exists(), f"Missing {compose_file}"

    content = compose_file.read_text(encoding="utf-8")
    config = yaml.safe_load(content)

    assert "services" in config
    services = config["services"]

    # Must contain api, dashboard, mlflow
    assert "api" in services
    assert "dashboard" in services
    assert "mlflow" in services

    # Port mappings
    assert "8000:8000" in services["api"]["ports"]
    assert "8501:8501" in services["dashboard"]["ports"]
    assert "5000:5000" in services["mlflow"]["ports"]

    # Dashboard depends on api
    assert "api" in services["dashboard"]["depends_on"]

    # Build context and dockerfiles
    api_build = services["api"]["build"]
    assert api_build["context"] == ".."
    assert (compose_file.parent / api_build["context"] / api_build["dockerfile"]).resolve().exists()

    dash_build = services["dashboard"]["build"]
    assert dash_build["context"] == ".."
    assert (
        (compose_file.parent / dash_build["context"] / dash_build["dockerfile"]).resolve().exists()
    )
