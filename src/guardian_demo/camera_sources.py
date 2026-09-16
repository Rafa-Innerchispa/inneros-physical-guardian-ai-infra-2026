from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from .frame_input import ALLOWED_IMAGE_TYPES, MAX_FRAME_BYTES, FramePayload
from .sima_contract import utc_now

CAMERA_SOURCES_ENV = "GUARDIAN_CAMERA_SOURCES_JSON"
_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,95}$")
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True)
class RemoteCameraSource:
    source_id: str
    label: str
    snapshot_url: str
    token_env: str | None = None
    allow_loopback_http: bool = False

    @classmethod
    def from_config(cls, source_id: str, value: object) -> "RemoteCameraSource":
        if not _SOURCE_ID_RE.fullmatch(source_id):
            raise ValueError(f"invalid camera source_id: {source_id}")
        if not isinstance(value, dict):
            raise ValueError(f"camera source {source_id} must be an object")
        label = value.get("label", source_id)
        snapshot_url = value.get("snapshot_url")
        token_env = value.get("token_env")
        allow_loopback_http = value.get("allow_loopback_http", False)
        if not isinstance(label, str) or not label.strip() or len(label) > 80:
            raise ValueError(f"camera source {source_id} has an invalid label")
        if not isinstance(snapshot_url, str) or not snapshot_url:
            raise ValueError(f"camera source {source_id} requires snapshot_url")
        parsed = urlparse(snapshot_url)
        is_loopback_http = (
            parsed.scheme == "http"
            and parsed.hostname in _LOOPBACK_HOSTS
            and allow_loopback_http is True
        )
        if parsed.scheme != "https" and not is_loopback_http:
            raise ValueError(f"camera source {source_id} requires HTTPS")
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"camera source {source_id} has an unsafe URL")
        if parsed.query or parsed.fragment:
            raise ValueError(f"camera source {source_id} URL cannot contain query or fragment data")
        if token_env is not None and (
            not isinstance(token_env, str) or not _ENV_NAME_RE.fullmatch(token_env)
        ):
            raise ValueError(f"camera source {source_id} has an invalid token_env")
        return cls(
            source_id=source_id,
            label=label.strip(),
            snapshot_url=snapshot_url,
            token_env=token_env,
            allow_loopback_http=allow_loopback_http is True,
        )

    def public_status(self) -> dict[str, str]:
        token_ready = not self.token_env or bool(os.environ.get(self.token_env, ""))
        return {
            "source_id": self.source_id,
            "label": self.label,
            "kind": "HOME_NVR_SNAPSHOT",
            "status": "READY" if token_ready else "BLOCKED",
            "truth": "UNVERIFIED",
        }

    def capture(self, *, now: datetime | None = None, timeout: float = 4.0) -> FramePayload:
        headers = {"Accept": "image/jpeg, image/png", "Cache-Control": "no-cache"}
        if self.token_env:
            token = os.environ.get(self.token_env, "")
            if not token:
                raise RuntimeError(f"camera source {self.source_id} credential is unavailable")
            headers["Authorization"] = f"Bearer {token}"
        request = Request(self.snapshot_url, headers=headers, method="GET")
        opener = build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"camera source returned HTTP {response.status}")
                if response.geturl() != self.snapshot_url:
                    raise RuntimeError("camera source redirects are not allowed")
                media_type = response.headers.get_content_type().lower()
                if media_type not in ALLOWED_IMAGE_TYPES:
                    raise RuntimeError("camera source returned an unsupported content type")
                image_bytes = response.read(MAX_FRAME_BYTES + 1)
        except (HTTPError, URLError, OSError, TimeoutError) as exc:
            raise RuntimeError(f"camera snapshot transport failed: {type(exc).__name__}") from exc
        timestamp = (now or utc_now()).isoformat()
        return FramePayload.from_bytes(
            frame_id=f"remote-{self.source_id}-{uuid4().hex[:16]}",
            source_id=self.source_id,
            captured_at=timestamp,
            image_type=media_type,
            image_bytes=image_bytes,
            now=now,
        )


class CameraSourceRegistry:
    def __init__(self, sources: dict[str, RemoteCameraSource] | None = None) -> None:
        self._sources = dict(sources or {})

    @classmethod
    def from_environment(cls) -> "CameraSourceRegistry":
        raw = os.environ.get(CAMERA_SOURCES_ENV, "").strip()
        if not raw:
            return cls()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{CAMERA_SOURCES_ENV} is not valid JSON") from exc
        if not isinstance(parsed, dict) or len(parsed) > 16:
            raise RuntimeError(f"{CAMERA_SOURCES_ENV} must contain at most 16 sources")
        try:
            sources = {
                source_id: RemoteCameraSource.from_config(source_id, config)
                for source_id, config in parsed.items()
            }
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        return cls(sources)

    def public_catalog(self) -> list[dict[str, str]]:
        return [source.public_status() for source in self._sources.values()]

    def capture(self, source_id: object, *, now: datetime | None = None) -> FramePayload:
        if not isinstance(source_id, str) or source_id not in self._sources:
            raise PermissionError("remote camera source_id is not allowlisted")
        return self._sources[source_id].capture(now=now)

    def describe(self) -> dict[str, Any]:
        return {
            "configured": bool(self._sources),
            "sources": self.public_catalog(),
            "transport": "HTTPS_SNAPSHOT",
            "client_supplied_urls": False,
        }
