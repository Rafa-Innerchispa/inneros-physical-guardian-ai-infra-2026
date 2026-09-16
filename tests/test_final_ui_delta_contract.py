from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _ui_files() -> tuple[str, str]:
    html = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "app" / "app.js").read_text(encoding="utf-8")
    return html, js


def test_final_ui_uses_backend_camera_and_inference_contract() -> None:
    html, js = _ui_files()

    assert "/api/camera/sources" in js
    assert "/api/inference/frame" in js
    assert "/api/inference/source" in js
    assert "/api/frame/infer" not in js
    assert "image_base64" in js
    assert "image_type" in js

    assert 'value="laptop-webcam"' in html
    assert 'value="remote-home-camera"' not in html
    assert "renderCameraSources" in js
    assert "arbitrary_urls_allowed" not in html


def test_final_ui_gates_detections_and_approval_on_current_backend_state() -> None:
    _, js = _ui_files()

    assert "payload?.frame_source?.frame_id" in js
    assert "payload?.inference?.source?.frame_id" in js
    assert "payload?.current?.frame_source?.source_id" in js
    assert "String(frameRef) === latestFrame.frameId" in js
    assert "String(sourceRef) === latestFrame.sourceId" in js
    assert "traceOrPayload?.current?.inference?.detections" in js
    assert "!detections.length || !detectionFrameMatches(payload)" in js

    assert 'action && trace.status === "AWAITING_APPROVAL"' in js
    assert "DENIED - NOTHING EXECUTED" in js
    assert "HISTORICAL BENCHMARK" in (ROOT / "app" / "index.html").read_text(encoding="utf-8")


def test_final_ui_clears_stale_state_on_new_input() -> None:
    _, js = _ui_files()

    assert "function resetRunView" in js
    assert "resetFrameUi({ clearFrame })" in js
    assert "els.sourceSelect.addEventListener" in js
    assert "resetRunView({ clearFrame: false })" in js
    assert "resetRunView();" in js
    assert "receiptFrame" in js
    assert "receiptReadback" in js
