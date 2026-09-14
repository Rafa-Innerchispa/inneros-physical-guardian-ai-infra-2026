from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_judge_ui_exposes_interruptible_lifecycle_and_truth_badge() -> None:
    html = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "app" / "app.js").read_text(encoding="utf-8")

    for marker in (
        'id="truthBadge"',
        'id="lifecyclePanel"',
        'id="lifecycleState"',
        'id="lifecycleTimeline"',
        'id="interruptBtn"',
        'id="reverifyBtn"',
        'id="resumeBtn"',
        'id="cancelBtn"',
    ):
        assert marker in html

    for route in (
        "/api/action/interrupt",
        "/api/action/reverify",
        "/api/action/resume",
        "/api/action/cancel",
    ):
        assert route in js

    assert "LIVE REAL" in js
    assert "SYNTHETIC FIXTURE" in js
    assert "Resume is fail-closed until safe-state re-verification succeeds." in html
