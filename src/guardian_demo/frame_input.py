from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .sima_contract import parse_utc_timestamp, sha256_bytes, utc_now

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_FRAME_BYTES = 1_000_000
MAX_JSON_BODY_BYTES = 1_400_000
MAX_WIDTH = 1280
MAX_HEIGHT = 720
MAX_CAPTURE_AGE_SECONDS = 15.0
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 12 or not data.startswith(b"\xff\xd8\xff"):
        raise ValueError("image content is not a JPEG")
    index = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index + 4 <= len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break
        segment_length = int.from_bytes(data[index:index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            raise ValueError("malformed JPEG segment")
        if marker in sof_markers:
            if segment_length < 7:
                raise ValueError("malformed JPEG dimensions")
            height = int.from_bytes(data[index + 3:index + 5], "big")
            width = int.from_bytes(data[index + 5:index + 7], "big")
            return width, height
        index += segment_length
    raise ValueError("JPEG dimensions are missing")


def image_dimensions(data: bytes, media_type: str) -> tuple[int, int]:
    if media_type == "image/png":
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            raise ValueError("image content is not a PNG")
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if media_type == "image/jpeg":
        return _jpeg_dimensions(data)
    raise ValueError("unsupported image media type")


def validate_image_bytes(data: bytes, media_type: str) -> tuple[int, int]:
    if media_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("image_type must be image/jpeg or image/png")
    if len(data) < 24:
        raise ValueError("image payload is too small")
    if len(data) > MAX_FRAME_BYTES:
        raise ValueError(f"image payload exceeds {MAX_FRAME_BYTES} bytes")
    width, height = image_dimensions(data, media_type)
    if width <= 0 or height <= 0 or width > MAX_WIDTH or height > MAX_HEIGHT:
        raise ValueError(f"image dimensions must be within {MAX_WIDTH}x{MAX_HEIGHT}")
    return width, height


@dataclass(frozen=True)
class FramePayload:
    frame_id: str
    source_id: str
    captured_at: str
    image_type: str
    image_bytes: bytes
    width: int
    height: int
    sha256: str

    @classmethod
    def from_json(cls, payload: object, *, now: datetime | None = None) -> "FramePayload":
        if not isinstance(payload, dict):
            raise ValueError("frame payload must be a JSON object")
        if any(field in payload for field in ("url", "image_url", "source_url", "rtsp_url")):
            raise ValueError("frame payloads cannot contain URLs")
        frame_id = payload.get("frame_id")
        source_id = payload.get("source_id")
        if not isinstance(frame_id, str) or not _ID_RE.fullmatch(frame_id):
            raise ValueError("invalid frame_id")
        if not isinstance(source_id, str) or not _ID_RE.fullmatch(source_id) or "://" in source_id:
            raise ValueError("invalid source_id")
        captured_at = payload.get("captured_at")
        captured = parse_utc_timestamp(captured_at, "captured_at")
        age = ((now or utc_now()) - captured).total_seconds()
        if age > MAX_CAPTURE_AGE_SECONDS:
            raise ValueError("captured frame is stale")
        if age < -2.0:
            raise ValueError("captured frame timestamp is in the future")
        image_type = payload.get("image_type")
        encoded = payload.get("image_base64")
        if not isinstance(image_type, str):
            raise ValueError("missing image_type")
        if not isinstance(encoded, str) or not encoded:
            raise ValueError("missing image_base64")
        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("image_base64 is malformed") from exc
        width, height = validate_image_bytes(image_bytes, image_type)
        declared_width = payload.get("width")
        declared_height = payload.get("height")
        if declared_width is not None and declared_width != width:
            raise ValueError("declared image width does not match content")
        if declared_height is not None and declared_height != height:
            raise ValueError("declared image height does not match content")
        return cls(
            frame_id=frame_id,
            source_id=source_id,
            captured_at=captured.isoformat(),
            image_type=image_type,
            image_bytes=image_bytes,
            width=width,
            height=height,
            sha256=sha256_bytes(image_bytes),
        )

    @classmethod
    def from_bytes(
        cls,
        *,
        frame_id: str,
        source_id: str,
        captured_at: str,
        image_type: str,
        image_bytes: bytes,
        now: datetime | None = None,
    ) -> "FramePayload":
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return cls.from_json(
            {
                "frame_id": frame_id,
                "source_id": source_id,
                "captured_at": captured_at,
                "image_type": image_type,
                "image_base64": encoded,
            },
            now=now,
        )

    def to_transport(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "source_id": self.source_id,
            "captured_at": self.captured_at,
            "image_type": self.image_type,
            "image_base64": base64.b64encode(self.image_bytes).decode("ascii"),
            "width": self.width,
            "height": self.height,
        }

    def source_provenance(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "source_id": self.source_id,
            "sha256": self.sha256,
            "media_type": self.image_type,
            "width": self.width,
            "height": self.height,
        }
