from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from guardian_demo.camera_sources import CameraSourceRegistry, RemoteCameraSource

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlBzv8AAAAASUVORK5CYII="
)


class SnapshotHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        self.server.authorization = self.headers.get("Authorization")  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(PNG_BYTES)))
        self.end_headers()
        self.wfile.write(PNG_BYTES)


def test_remote_source_config_rejects_unsafe_urls() -> None:
    for url in (
        "http://example.invalid/snapshot",
        "https://user:secret@example.invalid/snapshot",
        "https://example.invalid/snapshot?token=secret",
    ):
        with pytest.raises(ValueError):
            RemoteCameraSource.from_config("home-nvr-2", {"snapshot_url": url})


def test_registry_uses_only_operator_allowlisted_source_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GUARDIAN_CAMERA_SOURCES_JSON",
        json.dumps(
            {
                "home-nvr-2": {
                    "label": "Home camera 2",
                    "snapshot_url": "https://camera-proxy.invalid/snapshot",
                }
            }
        ),
    )
    registry = CameraSourceRegistry.from_environment()

    assert registry.public_catalog()[0]["source_id"] == "home-nvr-2"
    assert "snapshot_url" not in registry.public_catalog()[0]
    with pytest.raises(PermissionError, match="not allowlisted"):
        registry.capture("attacker-controlled")


def test_allowlisted_snapshot_is_transient_and_credentials_stay_server_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), SnapshotHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        monkeypatch.setenv("CAMERA_SNAPSHOT_TOKEN", "server-side-secret")
        source = RemoteCameraSource.from_config(
            "home-nvr-2",
            {
                "label": "Home camera 2",
                "snapshot_url": f"http://{host}:{port}/snapshot",
                "token_env": "CAMERA_SNAPSHOT_TOKEN",
                "allow_loopback_http": True,
            },
        )

        frame = source.capture()

        assert frame.source_id == "home-nvr-2"
        assert frame.image_bytes == PNG_BYTES
        assert frame.width == 1 and frame.height == 1
        assert server.authorization == "Bearer server-side-secret"  # type: ignore[attr-defined]
        assert "server-side-secret" not in json.dumps(source.public_status())
        assert "snapshot" not in json.dumps(source.public_status())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
