from __future__ import annotations

import base64
from datetime import timedelta

import pytest

from guardian_demo.frame_input import MAX_FRAME_BYTES, FramePayload, validate_image_bytes
from guardian_demo.sima_contract import utc_now

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlBzv8AAAAASUVORK5CYII="
)


def valid_payload() -> dict:
    return {
        "frame_id": "frame-input-001",
        "source_id": "laptop-webcam",
        "captured_at": utc_now().isoformat(),
        "image_type": "image/png",
        "image_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        "width": 1,
        "height": 1,
    }


def test_frame_payload_binds_identity_timestamp_dimensions_and_hash() -> None:
    frame = FramePayload.from_json(valid_payload())

    assert frame.width == 1
    assert frame.height == 1
    assert frame.source_provenance()["frame_id"] == "frame-input-001"
    assert len(frame.sha256) == 64


def test_frame_payload_rejects_stale_url_or_malformed_base64() -> None:
    stale = valid_payload()
    stale["captured_at"] = (utc_now() - timedelta(minutes=1)).isoformat()
    with pytest.raises(ValueError, match="stale"):
        FramePayload.from_json(stale)

    arbitrary_url = valid_payload()
    arbitrary_url["image_url"] = "https://example.invalid/frame.jpg"
    with pytest.raises(ValueError, match="cannot contain URLs"):
        FramePayload.from_json(arbitrary_url)

    malformed = valid_payload()
    malformed["image_base64"] = "not-base64!"
    with pytest.raises(ValueError, match="malformed"):
        FramePayload.from_json(malformed)


def test_frame_payload_rejects_unsupported_type_and_oversized_content() -> None:
    with pytest.raises(ValueError, match="image/jpeg or image/png"):
        validate_image_bytes(PNG_BYTES, "image/webp")
    with pytest.raises(ValueError, match="exceeds"):
        validate_image_bytes(b"x" * (MAX_FRAME_BYTES + 1), "image/png")


def test_declared_dimensions_must_match_actual_content() -> None:
    payload = valid_payload()
    payload["width"] = 640
    with pytest.raises(ValueError, match="width does not match"):
        FramePayload.from_json(payload)
