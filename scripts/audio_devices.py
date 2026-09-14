#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardian_demo.audio_devices import list_input_devices, render_device_report  # noqa: E402


def main() -> int:
    json_mode = "--json" in sys.argv[1:]
    try:
        devices = list_input_devices()
    except RuntimeError as exc:
        print(f"Audio preflight failed: {exc}", file=sys.stderr)
        return 2

    if json_mode:
        print(json.dumps([device.to_dict() for device in devices], sort_keys=True))
    else:
        print(render_device_report(devices))

    if not devices:
        return 2
    if not any(device.is_default for device in devices):
        print("WARNING: Windows/PyAudio did not report a default input device.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
