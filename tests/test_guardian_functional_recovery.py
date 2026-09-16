import base64
import hashlib
import pytest

from guardian_demo.engine import GuardianDemoEngine, MIN_LIVE_POLICY_CONFIDENCE
from guardian_demo.frame_input import FramePayload
from guardian_demo.models import Detection, RuntimeResult
from guardian_demo.runtime import TRUTH_MEASURED, DeterministicLocalRuntime
from guardian_demo.sima_contract import TRUTH_UNVERIFIED, utc_now

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlBzv8AAAAASUVORK5CYII="
)
PNG_SHA = hashlib.sha256(PNG_BYTES).hexdigest()


def _make_dummy_frame(source_id: str = "laptop-webcam") -> FramePayload:
    return FramePayload(
        frame_id=f"frame-{source_id}-test",
        source_id=source_id,
        image_type="image/png",
        image_bytes=PNG_BYTES,
        sha256=PNG_SHA,
        width=1,
        height=1,
        captured_at=utc_now().isoformat(),
    )


class MockMeasuredRuntime:
    def __init__(self, detections: list[Detection]):
        self.detections = tuple(detections)

    def infer_frame(self, *, scenario: str, frame: FramePayload) -> RuntimeResult:
        return RuntimeResult(
            runtime_id="sima-slot",
            provider="SiMa.ai",
            model="yolo26m-seg-bf16-b1",
            detections=self.detections,
            runtime_overhead_ms=31.25,
            inference_truth=TRUTH_MEASURED,
            notes="Mocked real SiMa Modalix execution",
            runtime="PyNeat 0.4.0 / SiMa MLA",
            device="SiMa.ai Modalix EV74",
            captured_at=frame.captured_at,
            inferred_at="2026-09-16T00:00:00Z",
            source=frame.source_provenance(),
            telemetry={"latency_ms": 31.25, "fps": 32.0, "output_tensors": 10, "truth": "MEASURED"},
            attestation={"runtime_verified": True, "device_verified": True},
        )


def test_1_webcam_frame_person_detection_visible(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("person", 0.88, (0.2, 0.2, 0.6, 0.8), None, None, 0)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="loitering_after_hours",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    trace = state["current"]
    assert trace["status"] == "AWAITING_APPROVAL"
    assert trace["truth"]["detections"] == TRUTH_MEASURED
    assert len(trace["inference"]["detections"]) == 1
    assert trace["inference"]["detections"][0]["label"] == "person"
    assert trace["proposed_action"]["action_type"] == "beacon_warning"


def test_2_webcam_frame_dog_cat_chair_detection_visible(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("dog", 0.85, (0.1, 0.1, 0.4, 0.5), None, None, 16),
        Detection("chair", 0.72, (0.5, 0.5, 0.8, 0.9), None, None, 56),
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="loitering_after_hours",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    trace = state["current"]
    assert len(trace["inference"]["detections"]) == 2
    assert trace["status"] == "POLICY_NOT_TRIGGERED"
    assert "Objects detected successfully" in trace["stages"][2]["summary"]


def test_3_gye_frame_measured_detection_visible(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("gye-dahua-ch2")
    mock_rt = MockMeasuredRuntime([
        Detection("car", 0.91, (0.1, 0.3, 0.7, 0.8), None, None, 2)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="restricted_zone_entry",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_REMOTE_SNAPSHOT",
    )
    trace = state["current"]
    assert trace["frame_source"]["source_id"] == "gye-dahua-ch2"
    assert len(trace["inference"]["detections"]) == 1
    assert trace["inference"]["detections"][0]["label"] == "car"


def test_4_bbox_normalized_coordinates(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("person", 0.80, (0.15, 0.25, 0.55, 0.75), None, None, 0)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="loitering_after_hours",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    det = state["current"]["inference"]["detections"][0]
    bbox = det["bbox"]
    assert len(bbox) == 4
    assert 0.0 <= bbox[0] < bbox[2] <= 1.0
    assert 0.0 <= bbox[1] < bbox[3] <= 1.0


def test_5_exact_frame_source_provenance_preserved(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("gye-dahua-ch3")
    mock_rt = MockMeasuredRuntime([
        Detection("person", 0.88, (0.2, 0.2, 0.5, 0.7), None, None, 0)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="repeated_access_attempt",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_REMOTE_SNAPSHOT",
    )
    trace = state["current"]
    assert trace["frame_source"]["frame_id"] == frame.frame_id
    assert trace["frame_source"]["source_id"] == "gye-dahua-ch3"
    assert trace["frame_source"]["sha256"] == frame.sha256


def test_6_person_above_threshold_triggers_awaiting_approval(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("person", 0.88, (0.2, 0.2, 0.5, 0.7), None, None, 0)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="repeated_access_attempt",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    trace = state["current"]
    assert trace["status"] == "AWAITING_APPROVAL"
    assert trace["proposed_action"]["action_type"] == "notify_operator"


def test_7_person_below_threshold_telemetry_only_no_action(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("person", 0.18, (0.2, 0.2, 0.5, 0.7), None, None, 0)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="loitering_after_hours",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    trace = state["current"]
    assert trace["status"] == "POLICY_NOT_TRIGGERED"
    assert "below Guardian policy threshold" in trace["stages"][2]["summary"]
    assert trace["proposed_action"] is None


def test_8_non_person_objects_visible_and_no_action(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("dog", 0.82, (0.1, 0.1, 0.4, 0.4), None, None, 16),
        Detection("cat", 0.79, (0.5, 0.5, 0.8, 0.8), None, None, 15),
        Detection("tv", 0.65, (0.6, 0.1, 0.9, 0.4), None, None, 62),
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    state = engine.run_frame(
        scenario="restricted_zone_entry",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    trace = state["current"]
    assert len(trace["inference"]["detections"]) == 3
    assert trace["status"] == "POLICY_NOT_TRIGGERED"
    assert "Objects detected successfully" in trace["stages"][2]["summary"]


def test_9_deny_operator_reject_nothing_executed(monkeypatch):
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("laptop-webcam")
    mock_rt = MockMeasuredRuntime([
        Detection("person", 0.88, (0.2, 0.2, 0.5, 0.7), None, None, 0)
    ])
    from guardian_demo import engine as eng_mod
    monkeypatch.setitem(eng_mod.RUNTIME_SLOTS, "sima-slot", mock_rt)

    engine.run_frame(
        scenario="loitering_after_hours",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_LOCAL_WEBCAM",
    )
    assert engine.current.status == "AWAITING_APPROVAL"

    state = engine.reject()
    trace = state["current"]
    assert trace["status"] == "REJECTED_SAFE"
    assert trace["decision"] == "REJECTED"
    assert trace["stages"][5]["truth"] == "NOT_EXECUTED" and "no physical output" in trace["stages"][5]["summary"]


def test_10_modalix_offline_camera_ready_guardian_blocked():
    engine = GuardianDemoEngine()
    frame = _make_dummy_frame("gye-dahua-ch2")
    state = engine.run_frame(
        scenario="loitering_after_hours",
        runtime_id="sima-slot",
        frame=frame,
        source_truth="ALLOWLISTED_REMOTE_SNAPSHOT",
    )
    trace = state["current"]
    assert trace["status"] == "INFERENCE_BLOCKED"
    assert trace["truth"]["detections"] == TRUTH_UNVERIFIED
    assert trace["stages"][1]["status"] == "blocked"
    assert trace["proposed_action"] is None
