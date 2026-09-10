# Sponsor Runtime Bridge Contract

The judge application keeps sponsor SDK code outside the presentation core. Each hardware integration runs as a loopback-only sidecar and exposes one endpoint.

## Endpoint

`POST /infer`

Request:

```json
{
  "scenario": "restricted_zone_entry",
  "frame_ref": "fixture://restricted_zone_entry/frame-001"
}
```

Response:

```json
{
  "model": "official-sdk-model-name",
  "truth": "MEASURED_SPONSOR_RUNTIME",
  "detections": [
    {
      "label": "person",
      "confidence": 0.97,
      "bbox": [0.10, 0.20, 0.40, 0.90],
      "track_id": "sdk-track-1",
      "zone": "equipment-zone"
    }
  ],
  "notes": "Optional factual runtime note"
}
```

Accepted `truth` values are intentionally limited:

- `MEASURED_SPONSOR_RUNTIME`: use only when the sidecar result is genuinely produced and timed on assigned sponsor hardware/runtime;
- `SPONSOR_RUNTIME_UNVERIFIED`: real integration path but measurement/provenance is not yet sufficient for a benchmark claim;
- `SIMULATED_SPONSOR_SDK`: mock/contract validation only.

Any other value is downgraded to `SPONSOR_RUNTIME_UNVERIFIED`.

## Environment binding

- SiMa.ai: `GUARDIAN_SIMA_RUNTIME_URL`
- Qualcomm: `GUARDIAN_QUALCOMM_RUNTIME_URL`
- Intel: `GUARDIAN_INTEL_RUNTIME_URL`

Only `localhost`, `127.0.0.1`, or `::1` URLs are accepted. This prevents the WebUI server from becoming an arbitrary outbound HTTP proxy and keeps sponsor credentials/SDK concerns in the local sidecar.

## On-site integration sequence

1. Bring up assigned hardware using the sponsor's official SDK and examples.
2. Produce one real inference outside Guardian and record exact hardware/runtime/model versions.
3. Wrap that call behind this `/infer` JSON contract.
4. Set the corresponding environment variable.
5. Refresh the WebUI. The sponsor slot becomes selectable automatically.
6. Run all three scenarios and verify evidence truth labels.
7. Add exact measured benchmark results only after repeatable hardware runs.

`scripts/mock_sponsor_sidecar.py` exists only to validate this contract before hardware arrives. It must not be used as sponsor benchmark evidence.
