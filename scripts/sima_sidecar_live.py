#!/usr/bin/env python3
"""SiMa.ai Modalix Live / Measured Sidecar Server for InnerOS Physical Guardian.

Provides POST /infer and GET /health for the SponsorRuntimeSlot boundary.
"""

from __future__ import annotations

import argparse
import logging
import os
from http.server import ThreadingHTTPServer

from guardian_demo.sima_adapter import SimaAdapterConfig, SimaLiveAdapter, make_sima_sidecar_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sima-sidecar-live")


def main() -> None:
    parser = argparse.ArgumentParser(description="SiMa.ai Modalix Guardian Sidecar")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8890)
    parser.add_argument("--mode", choices=["live", "fixture"], default="live")
    parser.add_argument(
        "--transport",
        choices=["auto", "ssh", "http"],
        default=os.environ.get("GUARDIAN_SIMA_TRANSPORT", "auto"),
    )
    parser.add_argument("--devkit-ip", default=os.environ.get("GUARDIAN_SIMA_DEVKIT_IP", ""))
    parser.add_argument("--inference-url", default=os.environ.get("GUARDIAN_SIMA_MODALIX_INFER_URL", ""))
    parser.add_argument("--model", default="yolo26m-seg-bf16-b1")
    parser.add_argument("--ssh-user", default=os.environ.get("GUARDIAN_SIMA_SSH_USER", "sima"))
    parser.add_argument("--ssh-port", type=int, default=int(os.environ.get("GUARDIAN_SIMA_SSH_PORT", "22")))
    parser.add_argument(
        "--model-archive",
        default=os.environ.get(
            "GUARDIAN_SIMA_MODEL_ARCHIVE",
            "/media/nvme/models/yolo26m-seg-bf16-b1.tar.gz",
        ),
    )
    parser.add_argument(
        "--model-sha256",
        default=os.environ.get(
            "GUARDIAN_SIMA_MODEL_SHA256",
            "41bebbecca2f20de40c76d4bc6656c3fe369f9c139929dad93922492efa9b591",
        ),
    )
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("The sponsor sidecar is loopback-only for security.")

    config = SimaAdapterConfig(
        mode=args.mode,
        transport=args.transport,
        devkit_ip=args.devkit_ip,
        model_name=args.model,
        inference_url=args.inference_url or None,
        ssh_user=args.ssh_user,
        ssh_port=args.ssh_port,
        model_archive=args.model_archive,
        model_sha256=args.model_sha256,
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
