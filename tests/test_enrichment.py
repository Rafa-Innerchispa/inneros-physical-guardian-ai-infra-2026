from __future__ import annotations

import pytest
from guardian_demo.enrichment import (
    GLOBAL_ENRICHMENT_ENGINE,
    EnrichedDetection,
    IdentityEnrichmentEngine,
)


def test_person_detection_fail_closed_unknown() -> None:
    engine = IdentityEnrichmentEngine()
    det = {"object_class": "person", "confidence": 0.91, "bbox": [0.1, 0.1, 0.4, 0.8]}
    enriched = engine.enrich_detection(det)

    assert isinstance(enriched, EnrichedDetection)
    assert enriched.object_class == "person"
    assert enriched.identity_type == "human"
    assert enriched.identity_label == "unknown person"
    assert enriched.identity_confidence is None
    assert enriched.identity_truth == "UNVERIFIED"

    # Invariant: NEVER fabricate Rafael without real biometric model running
    assert "Rafael" not in enriched.identity_label
    assert enriched.identity_confidence != 0.88


def test_pet_detection_fail_closed_unknown() -> None:
    engine = IdentityEnrichmentEngine()

    dog_det = {"object_class": "dog", "confidence": 0.85, "bbox": [0.2, 0.3, 0.5, 0.6]}
    enriched_dog = engine.enrich_detection(dog_det)
    assert enriched_dog.identity_type == "pet"
    assert enriched_dog.identity_label == "unknown dog"
    assert enriched_dog.identity_confidence is None
    assert "Max" not in enriched_dog.identity_label

    cat_det = {"object_class": "cat", "confidence": 0.78, "bbox": [0.3, 0.4, 0.6, 0.7]}
    enriched_cat = engine.enrich_detection(cat_det)
    assert enriched_cat.identity_type == "pet"
    assert enriched_cat.identity_label == "unknown cat"
    assert enriched_cat.identity_confidence is None


def test_non_person_non_pet_detection() -> None:
    engine = IdentityEnrichmentEngine()
    car_det = {"object_class": "car", "confidence": 0.95, "bbox": [0.0, 0.0, 1.0, 1.0]}
    enriched_car = engine.enrich_detection(car_det)
    assert enriched_car.identity_type == "none"
    assert enriched_car.identity_label == "none"
    assert enriched_car.identity_truth == "UNVERIFIED"


def test_enrich_detections_batch() -> None:
    engine = IdentityEnrichmentEngine()
    dets = [
        {"object_class": "person", "confidence": 0.9, "bbox": [0, 0, 100, 200]},
        {"object_class": "dog", "confidence": 0.8, "bbox": [10, 10, 50, 50]},
    ]
    batch = engine.enrich_detections(dets)
    assert len(batch) == 2
    assert batch[0]["identity_label"] == "unknown person"
    assert batch[1]["identity_label"] == "unknown dog"
