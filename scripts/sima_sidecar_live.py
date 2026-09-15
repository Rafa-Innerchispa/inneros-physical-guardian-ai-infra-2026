#!/usr/bin/env python3
"""SiMa.ai Modalix Live / Measured Sidecar Server for InnerOS Physical Guardian.

Provides POST /infer and GET /health for the SponsorRuntimeSlot boundary.
"""

from __future__ import annotations

import argparse
import logging
from http.server import ThreadingHTTPServer
from pathlib import Path

from guardian_demo.sima_adapter import SimaAdapterConfig, SimaLiveAdapter, make_sima_sidecar_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sima-sidecar-live")


def main() -> None:
    parser = argparse.ArgumentParser(description="SiMa.ai Modalix Guardian Sidecar")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8890)
    parser.add_argument("--mode", choices=["live", "fixture"], default="live")
    parser.add_argument("--devkit-ip", default="192.168.1.20")
    parser.add_argument("--model", default="yolo26m-seg-bf16-b1")
    parser.add_argument("--evidence", type=Path, default=Path("docs/sima_measured_evidence.json"))
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("The sponsor sidecar is loopback-only for security.")

    config = SimaAdapterConfig(
        mode=args.mode,
        devkit_ip=args.devkit_ip,
        model_name=args.model,
        evidence_path=args.evidence,
    )
    adapter = SimaLiveAdapter(config)
    handler_class = make_sima_sidecar_handler(adapter)
    server = ThreadingHTTPServer((args.host, args.port), handler_class)

    logger.info(f"SiMa Modalix Sidecar running at http://{args.host}:{args.port} [mode={args.mode}]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
