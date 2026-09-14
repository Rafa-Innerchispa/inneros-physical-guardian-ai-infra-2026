#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardian_demo.rehearsal import run_judge_rehearsal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exercise the full Guardian judge lifecycle and enforce optional live truth gates."
    )
    parser.add_argument("--scenario", default="restricted_zone_entry")
    parser.add_argument("--runtime", default="local-deterministic")
    parser.add_argument("--require-live-physical", action="store_true")
    parser.add_argument("--require-measured-sponsor", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        result = run_judge_rehearsal(
            scenario=args.scenario,
            runtime_id=args.runtime,
            require_live_physical=args.require_live_physical,
            require_measured_sponsor=args.require_measured_sponsor,
        )
    except Exception as exc:  # fail closed at the demo boundary
        result = {
            "ok": False,
            "mode": "STRICT_LIVE_GATE" if (args.require_live_physical or args.require_measured_sponsor) else "OFFLINE_REHEARSAL",
            "scenario": args.scenario,
            "runtime_id": args.runtime,
            "error": str(exc),
            "checks": [],
        }

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Judge rehearsal: {'PASS' if result['ok'] else 'FAIL'}")
        print(f"mode={result.get('mode')} scenario={result.get('scenario')} runtime={result.get('runtime_id')}")
        if result.get("error"):
            print(f"error={result['error']}")
        for check in result.get("checks", []):
            marker = "PASS" if check["ok"] else "FAIL"
            print(f"[{marker}] {check['name']}: {check.get('observed')}")
        if result.get("detections_truth"):
            print(f"detections_truth={result['detections_truth']}")
        if result.get("physical_io_truth"):
            print(f"physical_io_truth={result['physical_io_truth']}")
        if result.get("evidence_id"):
            print(f"evidence_id={result['evidence_id']}")

    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
