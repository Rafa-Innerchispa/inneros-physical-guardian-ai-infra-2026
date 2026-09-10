#!/usr/bin/env python3
"""Contract harness for the on-site sponsor SDK bridge.

This is intentionally simulated. Replace the response generation with the official
assigned sponsor SDK call while preserving POST /infer and the normalized JSON
response contract used by the judge application.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[mock-sponsor-sidecar] {fmt % args}")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/infer":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        request = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        payload = json.dumps(
            {
                "model": "mock-sponsor-contract-v1",
                "truth": "SIMULATED_SPONSOR_SDK",
                "detections": [
                    {
                        "label": "person",
                        "confidence": 0.95,
                        "bbox": [0.42, 0.18, 0.62, 0.91],
                        "track_id": "mock-sdk-track-01",
                        "zone": "restricted-lobby",
                    }
                ],
                "notes": f"Contract-only sidecar for scenario {request.get('scenario', 'unknown')}; not a sponsor benchmark.",
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8890)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("The sponsor contract harness is loopback-only by design.")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Mock sponsor sidecar: http://{args.host}:{args.port}/infer")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
