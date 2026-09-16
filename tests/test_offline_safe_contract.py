from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from guardian_demo.frame_input import FramePayload
from guardian_demo.server import GuardianDemoHandler, _source_catalog, _system_status


def test_source_id_catalog_contract() -> None:
    catalog = _source_catalog()
    sources = catalog["sources"]
    assert len(sources) >= 2
    for src in sources:
        assert "source_id" in src
        assert isinstance(src["source_id"], str)
        assert src["source_id"] in {"laptop-webcam", "local-prerecorded"} or src["source_id"].startswith("gye-dahua")


def test_frontend_source_id_contract_presence() -> None:
    root = Path(__file__).resolve().parents[1]
    js = (root / "app" / "app.js").read_text(encoding="utf-8")
    # Verify app.js uses src.source_id || src.id instead of hardcoded src.id
    assert "src.source_id" in js
    assert "s.source_id" in js


def test_sima_disconnected_system_status() -> None:
    status = _system_status()
    assert "sima_modalix" in status
    assert status["sima_modalix"]["status"] in {"OFFLINE", "BLOCKED"}
    assert status["sima_modalix"]["truth"] == "UNVERIFIED"
    assert "192.168.1.20" in status["sima_modalix"]["configured_target"]


def test_no_hardcoded_rafael_max_in_source_tree() -> None:
    root = Path(__file__).resolve().parents[1]
    enrichment_py = (root / "src" / "guardian_demo" / "enrichment.py").read_text(encoding="utf-8")
    assert "0.88" not in enrichment_py
    assert "0.85" not in enrichment_py
    assert "Rafael (Owner Profile)" not in enrichment_py
    assert "Max (Home Lab Dog)" not in enrichment_py


def test_camera_snapshot_route_without_sima_inference() -> None:
    root = Path(__file__).resolve().parents[1]
    server_py = (root / "src" / "guardian_demo" / "server.py").read_text(encoding="utf-8")
    assert "/api/camera/snapshot" in server_py
    assert "sima_inference" in server_py
    assert "OFFLINE / NOT RUN" in server_py
