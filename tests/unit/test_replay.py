"""
tests.unit.test_replay
======================
Unit and integration tests for Sentinel historical NASA SMAP/MSL replay service
and FastAPI replay endpoints (Task Phase 3).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from libs.contracts import Subsystem
from services.api.app import app
from services.data_plane.replay import (
    HistoricalReplayManager,
    get_replay_catalog,
    get_subsystem_for_channel,
)


def test_get_subsystem_for_channel_mappings():
    """Verify channel prefix and YAML config mappings across all 4 subsystems."""
    # YAML explicitly mapped
    assert get_subsystem_for_channel("P-1") == Subsystem.POWER
    assert get_subsystem_for_channel("T-1") == Subsystem.THERMAL
    assert get_subsystem_for_channel("A-1") == Subsystem.ATTITUDE
    assert get_subsystem_for_channel("C-1") == Subsystem.COMMUNICATIONS

    # MSL / Secondary channels
    assert get_subsystem_for_channel("P-10") == Subsystem.POWER
    assert get_subsystem_for_channel("T-4") == Subsystem.THERMAL
    assert get_subsystem_for_channel("M-1") == Subsystem.ATTITUDE
    assert get_subsystem_for_channel("D-14") == Subsystem.COMMUNICATIONS


def test_get_replay_catalog_discovery():
    """Verify discovery of SMAP and MSL channels and anomaly counts."""
    catalog = get_replay_catalog()
    assert "datasets" in catalog
    assert "SMAP" in catalog["datasets"]
    assert "MSL" in catalog["datasets"]

    smap_info = catalog["datasets"]["SMAP"]
    assert smap_info["total_channels"] >= 50
    p1 = next((ch for ch in smap_info["channels"] if ch["id"] == "P-1"), None)
    assert p1 is not None
    assert p1["subsystem"] == "power"
    assert p1["has_train"] is True
    assert p1["has_test"] is True
    assert p1["anomaly_count"] == 3

    msl_info = catalog["datasets"]["MSL"]
    assert msl_info["total_channels"] >= 25
    m1 = next((ch for ch in msl_info["channels"] if ch["id"] == "M-1"), None)
    assert m1 is not None
    assert m1["subsystem"] == "attitude"
    assert m1["anomaly_count"] >= 1


def test_replay_manager_sequential_execution():
    """Test sequential replay execution with actual SMAP P-1 telemetry."""
    async def _run():
        manager = HistoricalReplayManager()
        status = await manager.start(
            dataset="SMAP",
            split="test",
            channel="P-1",
            window_size=100,
            stride=10,
            speed_delay_ms=0,
            max_windows=3,
        )
        assert status["status"] == "running"
        assert status["total_windows"] == 3

        # Wait for completion
        if manager._task:
            await manager._task

        assert manager.status == "completed"
        assert manager.processed_windows == 3
        assert manager.failed_windows == 0
        assert manager.progress_percent == 100.0
        assert manager.latest_analysis is not None
        assert "decision" in manager.latest_analysis
        assert "audit_entry" in manager.latest_analysis
        assert len(manager.recent_history) == 3

    asyncio.run(_run())


def test_replay_manager_msl_execution():
    """Test sequential replay execution with actual MSL telemetry."""
    async def _run():
        manager = HistoricalReplayManager()
        status = await manager.start(
            dataset="MSL",
            split="train",
            channel="M-1",
            window_size=100,
            stride=10,
            speed_delay_ms=0,
            max_windows=2,
        )
        assert status["status"] == "running"
        assert status["total_windows"] == 2

        if manager._task:
            await manager._task

        assert manager.status == "completed"
        assert manager.processed_windows == 2
        assert manager.subsystem == Subsystem.ATTITUDE
        assert manager.latest_window is not None
        assert manager.latest_window["channel"] == "M-1"

    asyncio.run(_run())


def test_replay_manager_pause_resume_stop():
    """Test pause, resume, and stop controls."""
    async def _run():
        manager = HistoricalReplayManager()
        await manager.start(
            dataset="SMAP",
            split="test",
            channel="P-1",
            window_size=100,
            stride=10,
            speed_delay_ms=50,
            max_windows=10,
        )
        assert manager.status == "running"

        # Pause
        paused = await manager.pause()
        assert paused["status"] == "paused"

        # Resume
        resumed = await manager.resume()
        assert resumed["status"] == "running"

        # Stop
        stopped = await manager.stop()
        assert stopped["status"] == "stopped"

    asyncio.run(_run())


def test_api_replay_endpoints():
    """Test FastAPI /replay/* endpoints using TestClient."""
    client = TestClient(app)

    # 1. Get channels catalog
    resp_cat = client.get("/replay/channels")
    assert resp_cat.status_code == 200
    cat_data = resp_cat.json()
    assert "datasets" in cat_data
    assert "SMAP" in cat_data["datasets"]

    # 2. Get status initial
    resp_stat = client.get("/replay/status")
    assert resp_stat.status_code == 200

    # 3. Start replay with 2 windows
    resp_start = client.post(
        "/replay/start",
        json={
            "dataset": "SMAP",
            "split": "test",
            "channel": "P-1",
            "window_size": 100,
            "stride": 10,
            "speed_delay_ms": 0,
            "max_windows": 2,
        },
    )
    assert resp_start.status_code == 200
    start_data = resp_start.json()
    assert start_data["status"] == "running"

    # 4. Pause replay
    resp_pause = client.post("/replay/pause")
    assert resp_pause.status_code == 200

    # 5. Resume replay
    resp_resume = client.post("/replay/resume")
    assert resp_resume.status_code == 200

    # 6. Update config dynamically
    resp_cfg = client.post("/replay/config", json={"pause_on_anomaly": True, "speed_delay_ms": 200})
    assert resp_cfg.status_code == 200
    assert resp_cfg.json()["pause_on_anomaly"] is True
    assert resp_cfg.json()["speed_delay_ms"] == 200

    # 7. Stop replay
    resp_stop = client.post("/replay/stop")
    assert resp_stop.status_code == 200
    assert resp_stop.json()["status"] == "stopped"


def test_replay_edge_triggered_anomaly_pause_and_resume():
    """Verify that auto-pause on anomaly pauses once on entry and resumes through remaining anomalous windows."""
    async def _run():
        manager = HistoricalReplayManager()
        # P-1 anomaly interval starts around window 205. Start replay right at window 204 with pause_on_anomaly=True
        status = await manager.start(
            dataset="SMAP",
            split="test",
            channel="P-1",
            window_size=100,
            stride=10,
            speed_delay_ms=0,
            start_window=204,
            max_windows=210,
            pause_on_anomaly=True,
        )
        assert status["status"] == "running"

        # Give loop a brief moment to run into window 205
        await asyncio.sleep(0.1)

        # It must pause on window 205 (the anomaly entry)
        assert manager.status == "paused"
        assert manager.is_anomalous is True
        assert manager.current_window_index >= 205

        # Resume the replay
        resumed = await manager.resume()
        assert resumed["status"] == "running"

        # Wait for the remainder of windows up to max_windows (210) to finish without re-pausing on every window
        if manager._task:
            await manager._task

        assert manager.status == "completed"
        assert manager.processed_windows >= 5

    asyncio.run(_run())


def test_api_replay_invalid_dataset_rejected():
    """Verify invalid dataset name returns 400 Bad Request."""
    client = TestClient(app)
    resp = client.post(
        "/replay/start",
        json={"dataset": "UNKNOWN_DATASET", "channel": "P-1"},
    )
    assert resp.status_code == 400
