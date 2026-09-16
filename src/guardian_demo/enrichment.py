from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class EnrichedDetection:
    object_class: str
    confidence: float
    bbox: tuple[float, float, float, float]
    identity_type: str = "none"  # "human", "pet", "none"
    identity_label: str = "none"  # "unknown person", "unknown dog", "unknown cat", "none"
    identity_confidence: float | None = None
    identity_truth: str = "UNVERIFIED"  # Strictly UNVERIFIED without live biometric match model

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_class": self.object_class,
            "class": self.object_class,
            "label": self.object_class,
            "confidence": self.confidence,
            "bbox": list(self.bbox),
            "identity_type": self.identity_type,
            "identity_label": self.identity_label,
            "identity_confidence": self.identity_confidence,
            "identity_truth": self.identity_truth,
        }


class IdentityEnrichmentEngine:
    """Local, bounded identity enrichment layer applied after SiMa object detection.

    Architectural boundary:
    1. SiMa MLSoC produces raw object detections (person, dog, cat, car, etc.)
    2. IdentityEnrichmentEngine classifies identities fail-closed.
    3. Truth invariant: WITHOUT a verified live biometric inference model running on the crop,
       identities strictly default to:
       - 'unknown person' for person detections
       - 'unknown dog' / 'unknown cat' for pet detections
       NEVER fabricate a match score or person/pet profile name.
    """

    def __init__(self) -> None:
        self.status: str = "READY"
        self.biometric_matcher_active: bool = False

    def enrich_detection(
        self,
        raw_detection: Mapping[str, Any],
        image_bytes: bytes | None = None,
    ) -> EnrichedDetection:
        obj_class = str(
            raw_detection.get("object_class")
            or raw_detection.get("class")
            or raw_detection.get("label")
            or "object"
        ).lower()
        confidence = float(raw_detection.get("confidence", 0.0))
        raw_bbox = raw_detection.get("bbox", [0.0, 0.0, 1.0, 1.0])
        bbox = tuple(float(v) for v in raw_bbox)

        if obj_class == "person":
            # Without live biometric face match on the exact crop, truth is strictly UNKNOWN PERSON
            return EnrichedDetection(
                object_class="person",
                confidence=confidence,
                bbox=bbox,
                identity_type="human",
                identity_label="unknown person",
                identity_confidence=None,
                identity_truth="UNVERIFIED",
            )

        if obj_class in {"dog", "cat"}:
            # Without live pet ReID match on the exact crop, truth is strictly UNKNOWN PET
            return EnrichedDetection(
                object_class=obj_class,
                confidence=confidence,
                bbox=bbox,
                identity_type="pet",
                identity_label=f"unknown {obj_class}",
                identity_confidence=None,
                identity_truth="UNVERIFIED",
            )

        return EnrichedDetection(
            object_class=obj_class,
            confidence=confidence,
            bbox=bbox,
            identity_type="none",
            identity_label="none",
            identity_confidence=None,
            identity_truth="UNVERIFIED",
        )

    def enrich_detections(
        self,
        raw_detections: Sequence[Mapping[str, Any]],
        image_bytes: bytes | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for det in raw_detections:
            enriched = self.enrich_detection(det, image_bytes)
            results.append(enriched.to_dict())
        return results


GLOBAL_ENRICHMENT_ENGINE = IdentityEnrichmentEngine()
