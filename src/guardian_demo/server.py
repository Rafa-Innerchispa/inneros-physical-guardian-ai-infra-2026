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

from .engine import GuardianDemoEngine
from .voice import GuardianVoiceRouter, speechmatics_status


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "app"
ENGINE = GuardianDemoEngine()
VOICE = GuardianVoiceRouter(ENGINE)
VOICE_BRIDGE_TOKEN_ENV = "GUARDIAN_VOICE_BRIDGE_TOKEN"


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

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
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

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > 64_000:
            raise ValueError("request body too large")
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
            self._send_json(ENGINE.catalog())
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
            payload = self._read_json()
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
