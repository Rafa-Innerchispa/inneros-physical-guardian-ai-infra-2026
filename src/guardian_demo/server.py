from __future__ import annotations

import argparse
import base64
import hmac
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .camera_sources import CameraSourceRegistry
from .engine import GuardianDemoEngine
from .frame_input import MAX_JSON_BODY_BYTES, FramePayload
from .physical_io import PHYSICAL_IO
from .runtime import RUNTIME_SLOTS
from .sima_contract import TRUTH_MEASURED
from .voice import GuardianVoiceRouter, speechmatics_status


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "app"
ENGINE = GuardianDemoEngine()
VOICE = GuardianVoiceRouter(ENGINE)
VOICE_BRIDGE_TOKEN_ENV = "GUARDIAN_VOICE_BRIDGE_TOKEN"
LOCAL_FRAME_SOURCES = {
    "laptop-webcam": "LAPTOP_WEBCAM_CLIENT_CAPTURE",
    "local-prerecorded": "LOCAL_PRERECORDED_SOURCE",
}


class RequestBodyTooLarge(ValueError):
    """The declared request body exceeds the route's bounded contract."""


def _camera_sources() -> tuple[CameraSourceRegistry, str | None]:
    try:
        return CameraSourceRegistry.from_environment(), None
    except RuntimeError as exc:
        return CameraSourceRegistry(), str(exc)


def _source_catalog() -> dict[str, Any]:
    registry, error = _camera_sources()
    local = [
        {
            "source_id": "laptop-webcam",
            "label": "Laptop webcam",
            "kind": "LAPTOP_WEBCAM",
            "status": "READY",
            "truth": "UNVERIFIED",
        },
        {
            "source_id": "local-prerecorded",
            "label": "Local prerecorded media",
            "kind": "LOCAL_PRERECORDED_SOURCE",
            "status": "READY",
            "truth": "UNVERIFIED",
        },
    ]
    return {
        "sources": [*local, *registry.public_catalog()],
        "remote": registry.describe(),
        "configuration_error": error,
        "arbitrary_urls_allowed": False,
        "persistence": "NONE",
    }


def _system_status() -> dict[str, Any]:
    sima = RUNTIME_SLOTS["sima-slot"].status()
    io = PHYSICAL_IO.status()
    current = ENGINE.current
    measured_frame = bool(current and current.truth.get("detections") == TRUTH_MEASURED)
    evidence_ready = bool(ENGINE.latest_evidence)
    sima_state = str(sima.get("status", "BLOCKED"))
    io_state = "READY" if io.get("status") == "READY_CONFIGURED" else (
        "BLOCKED" if io.get("status") == "INVALID_LOCAL_BRIDGE_CONFIG" else "DEGRADED"
    )
    return {
        "camera": {"status": "READY", "truth": "UNVERIFIED"},
        "sima_modalix": {
            "status": "READY" if measured_frame else sima_state,
            "truth": "MEASURED" if measured_frame else "UNVERIFIED",
        },
        "mla": {
            "status": "READY" if measured_frame else sima_state,
            "truth": "MEASURED" if measured_frame else "UNVERIFIED",
        },
        "guardian": {"status": "READY", "truth": "REAL"},
        "physical_io": {
            "status": io_state,
            "truth": "REAL" if current and current.truth.get("physical_io") in {"PRODUCT_HTTP_READBACK", "REAL_LOW_VOLTAGE_HARDWARE"} else (
                "SIMULATED" if current and current.truth.get("physical_io") == "SIMULATED_REFERENCE_IO" else "UNVERIFIED"
            ),
        },
        "evidence": {
            "status": "READY" if evidence_ready else "OFFLINE",
            "truth": "MEASURED" if measured_frame and evidence_ready else "UNVERIFIED",
        },
    }


def _auth_config() -> tuple[str, str] | None | bool:
    """Return credentials, None when disabled, or False for invalid partial config."""
    username = os.environ.get("GUARDIAN_DEMO_USER", "")
    password = os.environ.get("GUARDIAN_DEMO_PASSWORD", "")
    if not username and not password:
        return None
    if not username or not password:
        return False
    return username, password


class GuardianDemoHandler(BaseHTTPRequestHandler):
    server_version = "GuardianDemo/0.3"

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep local demo logs minimal and free of request bodies or credentials.
        print(f"[guardian-demo] {self.address_string()} {fmt % args}")

    def _send_json(
        self,
        payload: dict[str, Any],
        status: int = HTTPStatus.OK,
        *,
        close_connection: bool = False,
    ) -> None:
        body = json.dumps(payload, indent=2, sort_keys=False).encode("utf-8")
        if close_connection:
            self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if close_connection:
            self.send_header("Connection", "close")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _challenge_auth(self) -> None:
        body = b"Authentication required."
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Basic realm="Guardian Judge Demo", charset="UTF-8"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_authorized(self) -> bool:
        config = _auth_config()
        if config is None:
            return True
        if config is False:
            return False
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(auth_header[6:], validate=True).decode("utf-8")
            supplied_user, supplied_password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return False
        expected_user, expected_password = config
        return hmac.compare_digest(supplied_user, expected_user) and hmac.compare_digest(
            supplied_password, expected_password
        )

    def _voice_source_truth(self) -> str:
        """Upgrade provenance only for a server-side authenticated live bridge."""
        expected = os.environ.get(VOICE_BRIDGE_TOKEN_ENV, "")
        supplied = self.headers.get("X-Guardian-Voice-Bridge", "")
        if expected and supplied and hmac.compare_digest(expected, supplied):
            return "SPEECHMATICS_LIVE_TRANSCRIPT"
        return "CLIENT_REPORTED_TRANSCRIPT"

    def _guard(self, path: str) -> bool:
        # Health stays public for container/platform readiness probes.
        if path == "/api/health":
            return True
        if self._is_authorized():
            return True
        self._challenge_auth()
        return False

    def _read_json(self, *, max_bytes: int = 64_000) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > max_bytes:
            raise RequestBodyTooLarge("request body too large")
        if self.headers.get_content_type().lower() != "application/json":
            raise ValueError("Content-Type must be application/json")
        raw = self.rfile.read(length)
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def _serve_static(self, request_path: str) -> None:
        relative = request_path.lstrip("/") or "index.html"
        candidate = (APP_ROOT / relative).resolve()
        if APP_ROOT.resolve() not in candidate.parents and candidate != APP_ROOT.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists() or not candidate.is_file():
            if "." not in Path(relative).name:
                candidate = APP_ROOT / "index.html"
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
        body = candidate.read_bytes()
        content_type, _ = mimetypes.guess_type(candidate.name)
        self.send_response(HTTPStatus.OK)
        value = content_type or "application/octet-stream"
        if content_type and content_type.startswith("text/"):
            value += "; charset=utf-8"
        self.send_header("Content-Type", value)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Permissions-Policy", "camera=(self), microphone=(self), geolocation=()")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._guard(path):
            return
        if path == "/api/health":
            config = _auth_config()
            self._send_json(
                {
                    "ok": True,
                    "service": "inneros-physical-guardian-ai-infra-2026",
                    "mode": "JUDGE_DEMO",
                    "build_window": "LIVE",
                    "access_control": "enabled"
                    if config not in (None, False)
                    else ("misconfigured" if config is False else "local/default"),
                }
            )
            return
        if path == "/api/catalog":
            catalog = ENGINE.catalog()
            catalog["camera_sources"] = _source_catalog()
            catalog["system_status"] = _system_status()
            self._send_json(catalog)
            return
        if path == "/api/camera/sources":
            self._send_json(_source_catalog())
            return
        if path == "/api/system/status":
            self._send_json(_system_status())
            return
        if path == "/api/state":
            self._send_json(ENGINE.state())
            return
        if path == "/api/voice/status":
            status = speechmatics_status()
            status["live_bridge_token_configured"] = bool(
                os.environ.get(VOICE_BRIDGE_TOKEN_ENV, "")
            )
            self._send_json(status)
            return
        if path == "/api/evidence/latest":
            if ENGINE.latest_evidence is None:
                self._send_json({"error": "no evidence yet"}, HTTPStatus.NOT_FOUND)
            else:
                self._send_json(ENGINE.latest_evidence)
            return
        if path.startswith("/api/"):
            self._send_json({"error": "unknown API route"}, HTTPStatus.NOT_FOUND)
            return
        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._guard(path):
            return
        try:
            max_bytes = MAX_JSON_BODY_BYTES if path == "/api/inference/frame" else 64_000
            payload = self._read_json(max_bytes=max_bytes)
            if path == "/api/demo/run":
                result = ENGINE.run(
                    str(payload.get("scenario", "loitering_after_hours")),
                    str(payload.get("runtime_id", "local-deterministic")),
                )
            elif path == "/api/demo/reset":
                result = ENGINE.reset()
            elif path == "/api/action/approve":
                result = ENGINE.approve()
            elif path == "/api/action/reject":
                result = ENGINE.reject()
            elif path == "/api/action/interrupt":
                result = ENGINE.interrupt()
            elif path == "/api/action/reverify":
                result = ENGINE.reverify()
            elif path == "/api/action/resume":
                result = ENGINE.resume()
            elif path == "/api/action/cancel":
                result = ENGINE.cancel()
            elif path == "/api/inference/frame":
                frame = FramePayload.from_json(payload)
                if frame.source_id not in LOCAL_FRAME_SOURCES:
                    raise PermissionError("frame source_id is not allowlisted for client submission")
                result = ENGINE.run_frame(
                    scenario=str(payload.get("scenario", "loitering_after_hours")),
                    runtime_id="sima-slot",
                    frame=frame,
                    source_truth=LOCAL_FRAME_SOURCES[frame.source_id],
                )
            elif path == "/api/inference/source":
                registry, configuration_error = _camera_sources()
                if configuration_error:
                    self._send_json(
                        {"status": "REMOTE_SOURCE_BLOCKED", "truth": "UNVERIFIED", "error": "remote camera configuration is invalid"},
                        HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                    return
                try:
                    frame = registry.capture(payload.get("source_id"))
                except RuntimeError:
                    self._send_json(
                        {"status": "REMOTE_SOURCE_BLOCKED", "truth": "UNVERIFIED", "error": "allowlisted remote snapshot is unavailable"},
                        HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                    return
                result = ENGINE.run_frame(
                    scenario=str(payload.get("scenario", "loitering_after_hours")),
                    runtime_id="sima-slot",
                    frame=frame,
                    source_truth="ALLOWLISTED_REMOTE_SNAPSHOT",
                )
            elif path == "/api/voice/intent":
                result = VOICE.route(
                    str(payload.get("transcript", "")),
                    provider=str(payload.get("provider", "speechmatics")),
                    source_truth=self._voice_source_truth(),
                )
            else:
                self._send_json({"error": "unknown API route"}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(result)
        except RequestBodyTooLarge as exc:
            self._send_json(
                {"error": str(exc), "fail_closed": True},
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                close_connection=True,
            )
        except PermissionError as exc:
            self._send_json({"error": str(exc), "fail_closed": True}, HTTPStatus.FORBIDDEN)
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)


def build_server(host: str = "127.0.0.1", port: int = 8787) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), GuardianDemoHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the InnerOS Physical Guardian hackathon judge demo")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host; defaults to local-only")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8787")))
    args = parser.parse_args()

    config = _auth_config()
    if config is False:
        raise SystemExit(
            "GUARDIAN_DEMO_USER and GUARDIAN_DEMO_PASSWORD must either both be set or both be unset"
        )

    server = build_server(args.host, args.port)
    print(f"InnerOS Physical Guardian judge demo: http://{args.host}:{args.port}")
    if config is None:
        print("Access control is disabled. Keep the default loopback binding for local judge demos.")
    else:
        print("HTTP Basic access control is enabled from environment variables.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
