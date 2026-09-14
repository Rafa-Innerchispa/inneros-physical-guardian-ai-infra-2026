from __future__ import annotations

import json

from guardian_demo import preflight


def test_optional_lanes_do_not_block_core_when_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(preflight, "_package_version", lambda _name: None)
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda _name: None)
    monkeypatch.delenv("SPEECHMATICS_API_KEY", raising=False)
    monkeypatch.delenv("GUARDIAN_VOICE_BRIDGE_TOKEN", raising=False)
    monkeypatch.delenv("GUARDIAN_SIMA_RUNTIME_URL", raising=False)
    monkeypatch.delenv("GUARDIAN_PHYSICAL_IO_URL", raising=False)
    monkeypatch.setattr(
        preflight,
        "_guardian_health_check",
        lambda _url, required: preflight.Check("guardian_health", "WARN", required, "not running"),
    )

    report = preflight.summarize(preflight.collect_checks())

    assert report["ok"] is True
    assert "speechmatics_sdk" in report["warnings"]
    assert "sima_sidecar" in report["warnings"]
    assert "physical_io_sidecar" in report["warnings"]


def test_required_speechmatics_lane_fails_without_sdk_or_key(monkeypatch) -> None:
    monkeypatch.setattr(preflight, "_package_version", lambda _name: None)
    monkeypatch.delenv("SPEECHMATICS_API_KEY", raising=False)
    monkeypatch.setattr(
        preflight,
        "_guardian_health_check",
        lambda _url, required: preflight.Check("guardian_health", "WARN", required, "not running"),
    )

    report = preflight.summarize(
        preflight.collect_checks(require_speechmatics=True)
    )

    assert report["ok"] is False
    assert "speechmatics_sdk" in report["required_failures"]
    assert "speechmatics_api_key" in report["required_failures"]


def test_preflight_never_serializes_secret_values(monkeypatch) -> None:
    sentinel = "THIS_SECRET_MUST_NEVER_APPEAR"
    monkeypatch.setenv("SPEECHMATICS_API_KEY", sentinel)
    monkeypatch.setenv("GUARDIAN_VOICE_BRIDGE_TOKEN", sentinel)
    monkeypatch.setattr(preflight, "_package_version", lambda _name: preflight.EXPECTED_SPEECHMATICS_VERSION)
    monkeypatch.setattr(
        preflight,
        "_guardian_health_check",
        lambda _url, required: preflight.Check("guardian_health", "WARN", required, "not running"),
    )

    report = preflight.summarize(preflight.collect_checks(require_speechmatics=True))
    rendered = json.dumps(report)

    assert sentinel not in rendered
    assert report["ok"] is True


def test_sidecars_must_stay_loopback(monkeypatch) -> None:
    monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", "https://example.com:9443")
    bad = preflight._loopback_url_check(
        "GUARDIAN_SIMA_RUNTIME_URL", "sima_sidecar", required=True
    )
    assert bad.status == "FAIL"

    monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", "http://127.0.0.1:9443")
    good = preflight._loopback_url_check(
        "GUARDIAN_SIMA_RUNTIME_URL", "sima_sidecar", required=True
    )
    assert good.status == "PASS"
    assert "127.0.0.1" not in good.detail


def test_mic_can_be_promoted_to_required_gate(monkeypatch) -> None:
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda _name: None)
    check = preflight._pyaudio_check(required=True)
    assert check.status == "FAIL"
    assert check.required is True
