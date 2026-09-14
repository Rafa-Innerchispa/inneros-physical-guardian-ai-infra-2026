from __future__ import annotations

from pathlib import Path

from guardian_demo.audio_devices import list_input_devices, render_device_report


ROOT = Path(__file__).resolve().parents[1]


class _FakeAudio:
    def __init__(self) -> None:
        self.terminated = False
        self.devices = [
            {
                "index": 0,
                "name": "Built-in Mic",
                "maxInputChannels": 2,
                "defaultSampleRate": 48000.0,
            },
            {
                "index": 1,
                "name": "Speakers",
                "maxInputChannels": 0,
                "defaultSampleRate": 48000.0,
            },
            {
                "index": 2,
                "name": "USB Mic",
                "maxInputChannels": 1,
                "defaultSampleRate": 16000.0,
            },
        ]

    def get_default_input_device_info(self):
        return self.devices[2]

    def get_device_count(self):
        return len(self.devices)

    def get_device_info_by_index(self, index: int):
        return self.devices[index]

    def terminate(self):
        self.terminated = True


class _FakePyAudioModule:
    def __init__(self) -> None:
        self.instance = _FakeAudio()

    def PyAudio(self):
        return self.instance


def test_audio_device_inventory_filters_outputs_and_marks_default() -> None:
    fake = _FakePyAudioModule()
    devices = list_input_devices(fake)

    assert [device.name for device in devices] == ["Built-in Mic", "USB Mic"]
    assert devices[0].channels == 2
    assert devices[1].default_sample_rate == 16000
    assert devices[1].is_default is True
    assert fake.instance.terminated is True


def test_audio_device_report_is_operator_readable() -> None:
    fake = _FakePyAudioModule()
    report = render_device_report(list_input_devices(fake))

    assert "USB Mic [DEFAULT]" in report
    assert "Speakers" not in report
    assert "16000Hz" in report


def test_windows_event_scripts_do_not_prompt_for_or_print_api_key() -> None:
    bootstrap = (ROOT / "scripts" / "windows_event_bootstrap.ps1").read_text(encoding="utf-8")
    start = (ROOT / "scripts" / "windows_event_start.ps1").read_text(encoding="utf-8")
    joined = bootstrap + "\n" + start

    assert "Read-Host" not in joined
    assert "SPEECHMATICS_API_KEY" in joined
    assert "Write-Host $env:SPEECHMATICS_API_KEY" not in joined
    assert "Write-Output $env:SPEECHMATICS_API_KEY" not in joined
    assert "GUARDIAN_VOICE_BRIDGE_TOKEN" in start


def test_windows_start_requires_bootstrap_venv() -> None:
    start = (ROOT / "scripts" / "windows_event_start.ps1").read_text(encoding="utf-8")
    assert ".venv\\Scripts\\python.exe" in start
    assert "--require-guardian" in start
    assert "--require-speechmatics" in start
    assert "--require-mic" in start
