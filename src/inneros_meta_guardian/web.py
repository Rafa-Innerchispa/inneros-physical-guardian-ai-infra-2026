"""Stdlib HTTP app; deliberately bound to localhost by default and unauthenticated."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import json
import os
import sys

from .engine import Guardian, LifecycleError

STATIC = Path(__file__).parent / "static"


class Handler(BaseHTTPRequestHandler):
    guardian: Guardian
    server_version = "InnerOSMetaGuardian/0.1"

    def _write(self, status: int, content: bytes, mime: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, obj: dict) -> None:
        self._write(status, json.dumps(obj, ensure_ascii=False).encode())

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise LifecycleError("Invalid Content-Length") from None
        if length <= 0 or length > 8192:
            raise LifecycleError("Request body required; maximum 8 KiB")
        try:
            val = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise LifecycleError("Invalid JSON body") from None
        if not isinstance(val, dict):
            raise LifecycleError("JSON object required")
        return val

    def do_GET(self):  # noqa: N802
        path = urlsplit(self.path).path
        if path in ("/", "/index.html"):
            self._static("index.html", "text/html; charset=utf-8")
        elif path == "/app.js":
            self._static("app.js", "application/javascript; charset=utf-8")
        elif path == "/styles.css":
            self._static("styles.css", "text/css; charset=utf-8")
        elif path == "/api/health":
            self._json(200, {"ok": True, "version": "0.1.0", "demo_only": True, "physical_actions": False, "meta_enabled": os.getenv("ALLOW_EXTERNAL_META", "false").lower() == "true" and bool(os.getenv("MODEL_API_KEY"))})
        elif path == "/api/state":
            self._json(200, {"scenarios": self.guardian.scenarios, "incidents": self.guardian.store.list_incidents(), "audit_integrity": self.guardian.store.verify(), "mode": "SIMULATION_ONLY", "project": "InnerOS Autonomous Infrastructure Guardian"})
        elif path == "/api/audit/verify":
            self._json(200, self.guardian.store.verify())
        elif path.startswith("/api/incidents/") and path.endswith("/evidence"):
            id = path.split("/")[3]
            try:
                self._json(200, self.guardian.evidence(id))
            except LifecycleError as exc:
                self._json(404, {"error": str(exc)})
        else:
            self._json(404, {"error": "Not found"})

    def _static(self, filename: str, mime: str) -> None:
        self._write(200, (STATIC / filename).read_bytes(), mime)

    def do_POST(self):  # noqa: N802
        path = urlsplit(self.path).path
        try:
            body = self._body()
            if path == "/api/incidents":
                self._json(201, self.guardian.ingest(body.get("scenario", "door_propped")))
                return
            parts = path.strip("/").split("/")
            if len(parts) != 4 or parts[:2] != ["api", "incidents"]:
                self._json(404, {"error": "Unknown route"})
                return
            _, _, id, action = parts
            if action == "analyze":
                result = self.guardian.analyze(id, body.get("mode", "deterministic"))
            elif action == "approve":
                result = self.guardian.approve(id, body.get("operator", ""), body.get("action", ""))
            elif action == "execute":
                result = self.guardian.execute(id)
            elif action == "verify":
                result = self.guardian.verify(id)
            else:
                self._json(404, {"error": "Unknown route"})
                return
            self._json(200, result)
        except (LifecycleError, ValueError) as exc:
            self._json(409, {"error": str(exc)})
        except Exception:
            # Avoid leaking remote API credentials or raw error bodies.
            self._json(500, {"error": "Internal application error"})

    def log_message(self, format: str, *args) -> None:
        # No bodies or tokens in logs.
        if os.getenv("GUARDIAN_ACCESS_LOG", "false").lower() == "true":
            super().log_message(format, *args)


def serve(host: str | None = None, port: int | None = None, db: str | None = None) -> None:
    host = host or os.getenv("HOST", "127.0.0.1")
    port = int(port or os.getenv("PORT", "8787"))
    if host not in ("127.0.0.1", "localhost", "::1") and os.getenv("GUARDIAN_UNSAFE_BIND") != "true":
        raise SystemExit("Refusing public bind: this demo has no authentication. Set GUARDIAN_UNSAFE_BIND=true only in an isolated test network.")
    database = db or os.getenv("GUARDIAN_DB", "runtime/guardian.db")
    guardian = Guardian(database)
    class ServerHandler(Handler):
        pass
    ServerHandler.guardian = guardian
    server = ThreadingHTTPServer((host, port), ServerHandler)
    print(f"InnerOS Meta Guardian demo at http://{host}:{port} (fixtures only, no physical I/O)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
