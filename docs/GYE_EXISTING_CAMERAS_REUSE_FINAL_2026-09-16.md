# GYE Existing Cameras Reuse Final

Date: 2026-09-16

Status reported by AntiGravity: `GYE_TWO_CAMERA_E2E_PASS`.

This document records the final AntiGravity runtime report provided by the operator. The raw evidence artifact referenced by AntiGravity (`gye_existing_cameras_reuse_evidence.json`) was not found in the GitHub branches searched at the time this checkpoint was written, so this document preserves the reported facts while keeping that artifact-durability gap explicit.

## Infrastructure and security

- AMD .5 node active and reachable over Tailscale.
- Existing Physical Guardian Visual Watch service on AMD .5 confirmed active with the real Dahua local RTSP pipeline.
- Bounded private snapshot bridge reported on the Tailnet, authenticated by header token.
- No public DVR port exposure reported.
- No credentials leaked in the report.
- Hackathon camera sources configured as `gye-dahua-ch2` and `gye-dahua-ch3`.

## Reported E2E path

Dahua Ch2/Ch3 -> AMD .5 -> private Tailscale bridge -> SF laptop host -> Modalix DevKit EV74 -> PyNeat 0.4.0 / MLA -> YOLO26m outputs -> Guardian Demo Engine.

## Reported channel results

### GYE Dahua Ch2

- dimensions: 352x240
- payload: 7,570 bytes
- snapshot latency: 456.5 ms
- Modalix MLA execution: 31.36 ms
- execution status: `REAL_TARGET_MLA_DECODE_SUCCESS`
- output tensors: 10
- detections: 17
- provenance: PASS

### GYE Dahua Ch3

- dimensions: 352x240
- payload: 6,792 bytes
- snapshot latency: 451.0 ms
- Modalix MLA execution: 31.36 ms
- execution status: `REAL_TARGET_MLA_DECODE_SUCCESS`
- output tensors: 10
- detections: 16
- provenance: PASS

## Reported scorecard

- MCP access: PASS
- AMD .5 reachable: PASS
- existing camera ch2: PASS
- existing camera ch3: PASS
- existing snapshot path reusable: YES
- Tailscale .5 reachable from SF: PASS
- ch2 -> Modalix: PASS
- ch3 -> Modalix: PASS
- ch2 Guardian provenance: PASS
- ch3 Guardian provenance: PASS
- secrets exposed: NO
- public DVR ports opened: NO

## Final verdict

`GYE_TWO_CAMERA_E2E_PASS`

## Durability note

The AntiGravity report referenced `gye_existing_cameras_reuse_evidence.json`. That raw JSON artifact should be committed or otherwise durably stored before final submission if available. This document is a durable checkpoint of the reported result, not a replacement for the original raw evidence artifact.
