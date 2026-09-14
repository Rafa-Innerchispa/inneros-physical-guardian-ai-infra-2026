from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardian_demo.sima_onsite import build_evidence_record, dumps_record  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create truth-gated SiMa.ai benchmark/evidence JSON for Guardian"
    )
    parser.add_argument("--hardware", default="")
    parser.add_argument("--platform-version", default="")
    parser.add_argument("--neat-version", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--sample-count", type=int, default=0)
    parser.add_argument("--latency-p50-ms", type=float)
    parser.add_argument("--latency-p95-ms", type=float)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--power-w", type=float)
    parser.add_argument("--energy-j", type=float)
    parser.add_argument("--evidence-id", default="")
    parser.add_argument("--source-json", type=Path)
    parser.add_argument(
        "--measured",
        action="store_true",
        help="Request MEASURED_SPONSOR_RUNTIME; gate downgrades incomplete evidence automatically",
    )
    parser.add_argument("--output", type=Path, help="Write record to a JSON file; stdout otherwise")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.source_json and not args.source_json.is_file():
        raise SystemExit(f"source JSON not found: {args.source_json}")

    record = build_evidence_record(
        hardware=args.hardware,
        platform_version=args.platform_version,
        neat_version=args.neat_version,
        model=args.model,
        sample_count=args.sample_count,
        latency_p50_ms=args.latency_p50_ms,
        latency_p95_ms=args.latency_p95_ms,
        fps=args.fps,
        power_w=args.power_w,
        energy_j=args.energy_j,
        evidence_id=args.evidence_id,
        source_json=args.source_json,
        measured_requested=args.measured,
    )
    payload = dumps_record(record)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote SiMa evidence: {args.output}")
        print(f"truth={record['truth']} measured={record['measured']}")
    else:
        print(payload, end="")

    return 0 if record["measured"] or not args.measured else 2


if __name__ == "__main__":
    raise SystemExit(main())
