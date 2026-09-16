from __future__ import annotations

from guardian_demo.enrichment import IdentityEnrichmentEngine, EnrichedDetection


def test_enrichment_unrecognized_person_defaults_to_unknown_person() -> None:
    engine = IdentityEnrichmentEngine()
    raw = {"object_class": "person", "confidence": 0.85, "bbox": [0.1, 0.2, 0.5, 0.6]}
    enriched = engine.enrich_detection(raw)

    assert enriched.object_class == "person"
    assert enriched.confidence == 0.85
    assert enriched.identity_type == "human"
    assert enriched.identity_label == "unknown person"
    assert enriched.identity_truth == "LOCAL_ENRICHMENT"


def test_enrichment_recognized_person_attaches_known_profile() -> None:
    engine = IdentityEnrichmentEngine()
    raw = {"object_class": "person", "confidence": 0.92, "bbox": [0.1, 0.1, 0.4, 0.8]}
    enriched = engine.enrich_detection(raw, known_profile_hint="rafael_owner")

    assert enriched.object_class == "person"
    assert enriched.identity_type == "human"
    assert enriched.identity_label == "Rafael (Owner Profile)"
    assert enriched.identity_confidence == 0.88
    assert enriched.identity_truth == "LOCAL_ENRICHMENT"


def test_enrichment_pet_recognition_known_and_unknown() -> None:
    engine = IdentityEnrichmentEngine()
    
    # Unknown dog
    raw_dog = {"object_class": "dog", "confidence": 0.77, "bbox": [0.2, 0.3, 0.4, 0.5]}
    enriched_dog = engine.enrich_detection(raw_dog)
    assert enriched_dog.object_class == "dog"
    assert enriched_dog.identity_type == "pet"
    assert enriched_dog.identity_label == "unknown dog"

    # Known enrolled dog
    enriched_max = engine.enrich_detection(raw_dog, known_profile_hint="lab_dog")
    assert enriched_max.identity_label == "Max (Home Lab Dog)"
    assert enriched_max.identity_confidence == 0.85

    # Unknown cat
    raw_cat = {"object_class": "cat", "confidence": 0.81, "bbox": [0.1, 0.1, 0.3, 0.3]}
    enriched_cat = engine.enrich_detection(raw_cat)
    assert enriched_cat.object_class == "cat"
    assert enriched_cat.identity_type == "pet"
    assert enriched_cat.identity_label == "unknown cat"


def test_enrichment_non_biometric_objects_are_unverified() -> None:
    engine = IdentityEnrichmentEngine()
    raw_chair = {"object_class": "chair", "confidence": 0.65, "bbox": [0.3, 0.3, 0.6, 0.7]}
    enriched = engine.enrich_detection(raw_chair)

    assert enriched.object_class == "chair"
    assert enriched.identity_type == "none"
    assert enriched.identity_label == "none"
    assert enriched.identity_truth == "UNVERIFIED"
