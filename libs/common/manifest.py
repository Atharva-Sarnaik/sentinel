"""
libs.common.manifest
====================
Run manifest creation, experiment tracking, and model registry storage.

Ties together MLflow run IDs (if MLflow is available), config hashes,
dataset hashes, and git commits to create immutable RunManifest records (task T1.7).
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from libs.common.helpers import utc_now
from libs.contracts import RunManifest

logger = logging.getLogger(__name__)

DEFAULT_RUNS_DIR = Path("artifacts/runs")


def compute_sha256(data: bytes | str) -> str:
    """Compute hex SHA256 digest of bytes or string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: Path | str) -> str:
    """Compute hex SHA256 digest of a file on disk."""
    p = Path(path)
    if not p.is_file():
        return "non-file-or-missing"
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_current_git_commit() -> str | None:
    """Retrieve the current HEAD git commit hash, or None if unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return None


class ManifestStore:
    """
    Local filesystem and MLflow registry storage for RunManifest instances.
    """

    def __init__(self, root_dir: Path | str = DEFAULT_RUNS_DIR) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, manifest: RunManifest) -> Path:
        """
        Save a RunManifest to disk as a JSON artifact under root_dir/{run_id}/manifest.json.
        """
        run_folder = self.root_dir / manifest.run_id
        run_folder.mkdir(parents=True, exist_ok=True)
        dest = run_folder / "manifest.json"

        data = json.loads(manifest.model_dump_json())
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

        return dest

    def get(self, run_id: str) -> RunManifest | None:
        """Retrieve a RunManifest by its run_id."""
        dest = self.root_dir / run_id / "manifest.json"
        if not dest.is_file():
            return None

        with open(dest, encoding="utf-8") as f:
            data = json.load(f)

        return RunManifest.model_validate(data)

    def list_all(self) -> list[RunManifest]:
        """List all stored RunManifests, sorted newest first."""
        manifests: list[RunManifest] = []
        for path in self.root_dir.glob("*/manifest.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                manifests.append(RunManifest.model_validate(data))
            except Exception as e:
                logger.warning("Failed to load manifest at %s: %s", path, e)

        return sorted(manifests, key=lambda m: m.created_at, reverse=True)


def create_run_manifest(
    description: str,
    config_data: dict[str, Any] | str,
    dataset_identifier: str = "NASA-SMAP-synthetic-or-stream",
    mlflow_experiment_id: str = "sentinel-specialists",
    mlflow_run_ids: dict[str, str] | None = None,
    artifact_dir: Path | None = None,
) -> RunManifest:
    """
    Construct a validated RunManifest tying together code, config, and dataset hashes.
    """
    if isinstance(config_data, dict):
        config_serialized = json.dumps(config_data, sort_keys=True)
    else:
        config_serialized = str(config_data)

    config_hash = compute_sha256(config_serialized)
    dataset_dvc_hash = compute_sha256(dataset_identifier)
    git_commit = get_current_git_commit()

    run_ids = mlflow_run_ids or {
        "power": "local-run-power",
        "thermal": "local-run-thermal",
        "attitude": "local-run-attitude",
        "communications": "local-run-comms",
    }

    return RunManifest(
        description=description,
        dataset_dvc_hash=dataset_dvc_hash,
        config_hash=config_hash,
        mlflow_experiment_id=mlflow_experiment_id,
        mlflow_run_ids=run_ids,
        git_commit=git_commit,
        artifact_dir=artifact_dir,
        created_at=utc_now(),
    )
