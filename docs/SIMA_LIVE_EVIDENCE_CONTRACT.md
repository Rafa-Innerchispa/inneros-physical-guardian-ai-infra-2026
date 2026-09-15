# SiMa Live Evidence Contract

Status: **offline deterministic gate** for AntiGravity measured live output. No hardware mutation.

## Purpose

`scripts/sima_live_evidence_gate.py` validates one JSON evidence file before judge rehearsal or handoff. The gate is strict about live truth labels, SiMa sponsor runtime, Modalix device identity, detection shape, freshness, and measured metric provenance.

## Schema

```json
{
  "schema": "inneros.guardian.sima.live_evidence.v1",
  "captured_at": "2026-09-15T19:05:00+00:00",
  "frame_timestamp": "2026-09-15T19:04:59.950000+00:00",
  "truth": "MEASURED_SPONSOR_RUNTIME",
  "live": true,
  "sponsor_runtime": "sima",
  "device": {
    "kind": "modalix",
    "identifier": "Modalix MLSoC DevKit"
  },
  "model": "yolo_v8s",
  "input_source": "camera:/dev/video0",
  "max_staleness_ms": 5000,
  "detections": [
    {
      "class": "person",
      "confidence": 0.91,
      "bbox": [0.15, 0.22, 0.48, 0.81]
    }
  ],
  "metrics": {
    "latency_ms": 4.2,
    "fps": 118.0
  },
  "metrics_provenance": "antigravity_adapter_sidecar_log",
  "provenance": {
    "adapter": "antigravity-sima-infer",
    "evidence_id": "LIVE-001"
  }
}
```

## Required fields

| Field | Rule |
|-------|------|
| `schema` | Must equal `inneros.guardian.sima.live_evidence.v1` |
| `truth` / `live` | Live evidence must use `MEASURED_SPONSOR_RUNTIME` or `LIVE_SPONSOR_RUNTIME`, or `live=true` |
| `sponsor_runtime` | Must identify SiMa (`sima`, `sima.ai`, `sima_ai`) |
| `device.identifier` | Modalix or explicit onsite hardware identifier |
| `model` | Exact compiled model name |
| `input_source` | Exact camera/file/stream source |
| `captured_at`, `frame_timestamp` | ISO-8601 timestamps |
| `detections` | Non-empty list with at least one valid detection |
| detection.class/label | Non-empty class label |
| detection.confidence | Numeric value in `[0, 1]` |
| detection.bbox | Four normalized coordinates with `x2 > x1`, `y2 > y1` |
| `provenance.adapter` | Source adapter name for audit trail |

## Optional measured metrics

`metrics.latency_ms`, `metrics.fps`, and related timing fields are optional. If any metric object is present, `metrics_provenance` is required. Never invent measured values in fixtures or examples.

## Rejections

The gate fails closed on:

- simulated/fixture truth presented as live
- malformed bbox or confidence outside `[0, 1]`
- stale frame relative to `max_staleness_ms`
- non-SiMa sponsor runtime when live evidence is required
- zero detections
- measured metrics without provenance

## CLI

```bash
python3 scripts/sima_live_evidence_gate.py path/to/live-evidence.json
python3 scripts/sima_live_evidence_gate.py tests/fixtures/sima_live_evidence/simulated_fixture.json --allow-simulated
```

Exit codes:

- `0` PASS
- `2` FAIL validation
- `1` unreadable or invalid JSON root

## AntiGravity handoff

1. Capture measured live inference output from the SiMa `/infer` adapter path.
2. Serialize to this schema without embedding raw vendor blobs; keep hashes/provenance instead.
3. Run the gate locally before judge rehearsal:

```bash
python3 scripts/sima_live_evidence_gate.py /tmp/sima-live-evidence.json
python3 scripts/judge_rehearsal.py --require-measured-sponsor --json
```

4. Keep simulated fixtures under `tests/fixtures/sima_live_evidence/` clearly labeled with `SIMULATED_*` truth values.

## Related read-only contracts

- `scripts/sima_capture_evidence.py`
- `scripts/judge_rehearsal.py`
- `src/guardian_demo/sima_onsite.py`
- `src/guardian_demo/rehearsal.py`
