from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardian_demo.sima_onsite import (  # noqa: E402
    SIMA_DOCS,
    build_bringup_plan,
    collect_sima_readiness,
    validate_devkit_ip,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only SiMa.ai Modalix readiness probe and bring-up plan"
    )
    parser.add_argument("--probe-device", action="store_true", help="Run `sima-cli device discover`")
    parser.add_argument("--probe-modelzoo", action="store_true", help="Run `sima-cli modelzoo list`")
    parser.add_argument("--devkit-ip", default="", help="Optional already-known Modalix IP for plan generation")
    parser.add_argument("--require-cli", action="store_true", help="Exit non-zero when sima-cli is missing")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    devkit_ip = validate_devkit_ip(args.devkit_ip) if args.devkit_ip else None
    checks = collect_sima_readiness(
        probe_device=args.probe_device,
        probe_modelzoo=args.probe_modelzoo,
    )
    cli_ok = bool(checks and checks[0].status == "PASS")
    report = {
        "ok": cli_ok or not args.require_cli,
        "checks": [asdict(item) for item in checks],
        "bringup_plan": build_bringup_plan(devkit_ip),
        "official_docs": SIMA_DOCS,
        "safety": {
            "read_only": True,
            "does_not_login": True,
            "does_not_install": True,
            "does_not_update_firmware": True,
            "does_not_print_credentials": True,
        },
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("InnerOS Physical Guardian - SiMa.ai onsite preflight\n")
        for item in checks:
            print(f"{item.status:4} {item.name}: {item.detail}")
        print("\nRecommended official bring-up sequence:")
        for index, command in enumerate(report["bringup_plan"], start=1):
            print(f"  {index}. {command}")
        print("\nThis probe is read-only. Install/login/firmware operations are intentionally not automated.")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
