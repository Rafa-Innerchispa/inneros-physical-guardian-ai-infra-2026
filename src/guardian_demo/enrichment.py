from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class EnrichedDetection:
    object_class: str
    confidence: float
    bbox: tuple[float, float, float, float]
    identity_type: str = "none"  # "human", "pet", "none"
    identity_label: str = "none"  # e.g., "unknown person", "Rafael L.", "unknown dog"
    identity_confidence: float | None = None
    identity_truth: str = "UNVERIFIED"  # "LOCAL_ENRICHMENT", "REFERENCE", "UNVERIFIED"

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
    2. IdentityEnrichmentEngine optionally attaches identity attributes.
    3. SiMa hardware telemetry and identity truth remain strictly separate.
    """

    def __init__(self) -> None:
        self.human_profiles: dict[str, dict[str, Any]] = {}
        self.pet_profiles: dict[str, dict[str, Any]] = {}
        self.status: str = "READY"
        self._load_default_enrolled_profiles()

    def _load_default_enrolled_profiles(self) -> None:
        # Default enrolled known human profile for controlled local environment
        self.human_profiles["rafael_owner"] = {
            "name": "Rafael (Owner Profile)",
            "type": "human",
            "enrolled": True,
            "match_threshold": 0.82,
            "metadata": {"role": "site_operator", "zone_access": "all_hours"},
        }
        # Default enrolled known pet profile
        self.pet_profiles["lab_dog"] = {
            "name": "Max (Home Lab Dog)",
            "species": "dog",
            "type": "pet",
            "enrolled": True,
            "match_threshold": 0.65,
            "metadata": {"species": "dog", "household": "primary"},
        }

    def enroll_human(
        self,
        profile_id: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.human_profiles[profile_id] = {
            "name": name,
            "type": "human",
            "enrolled": True,
            "match_threshold": 0.82,
            "metadata": metadata or {},
        }

    def enroll_pet(
        self,
        profile_id: str,
        name: str,
        species: str = "dog",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.pet_profiles[profile_id] = {
            "name": name,
            "species": species.lower(),
            "type": "pet",
            "enrolled": True,
            "match_threshold": 0.65,
            "metadata": metadata or {},
        }

    def enrich_detection(
        self,
        raw_detection: Mapping[str, Any],
        image_bytes: bytes | None = None,
        *,
        known_profile_hint: str | None = None,
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
            if known_profile_hint and known_profile_hint in self.human_profiles:
                profile = self.human_profiles[known_profile_hint]
                return EnrichedDetection(
                    object_class="person",
                    confidence=confidence,
                    bbox=bbox,
                    identity_type="human",
                    identity_label=profile["name"],
                    identity_confidence=0.88,
                    identity_truth="LOCAL_ENRICHMENT",
                )
            return EnrichedDetection(
                object_class="person",
                confidence=confidence,
                bbox=bbox,
                identity_type="human",
                identity_label="unknown person",
                identity_confidence=None,
                identity_truth="LOCAL_ENRICHMENT",
            )

        if obj_class in {"dog", "cat"}:
            if known_profile_hint and known_profile_hint in self.pet_profiles:
                profile = self.pet_profiles[known_profile_hint]
                if profile.get("species") == obj_class or obj_class == "dog":
                    return EnrichedDetection(
                        object_class=obj_class,
                        confidence=confidence,
                        bbox=bbox,
                        identity_type="pet",
                        identity_label=profile["name"],
                        identity_confidence=0.85,
                        identity_truth="LOCAL_ENRICHMENT",
                    )
            return EnrichedDetection(
                object_class=obj_class,
                confidence=confidence,
                bbox=bbox,
                identity_type="pet",
                identity_label=f"unknown {obj_class}",
                identity_confidence=None,
                identity_truth="LOCAL_ENRICHMENT",
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
        *,
        known_profile_hint: str | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for det in raw_detections:
            enriched = self.enrich_detection(det, image_bytes, known_profile_hint=known_profile_hint)
            results.append(enriched.to_dict())
        return results


GLOBAL_ENRICHMENT_ENGINE = IdentityEnrichmentEngine()
