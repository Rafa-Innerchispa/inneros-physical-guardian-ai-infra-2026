from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class InputDevice:
    index: int
    name: str
    channels: int
    default_sample_rate: int
    is_default: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def list_input_devices(pyaudio_module: Any | None = None) -> list[InputDevice]:
    """Return available microphone/input devices without recording audio.

    Importing PyAudio is intentionally deferred so the core Guardian demo keeps
    its zero-dependency behavior when the optional voice lane is not installed.
    """

    if pyaudio_module is None:
        try:
            import pyaudio as pyaudio_module  # type: ignore[no-redef]
        except ImportError as exc:
            raise RuntimeError(
                "PyAudio is not installed. Install the speechmatics-live optional dependency first."
            ) from exc

    audio = pyaudio_module.PyAudio()
    try:
        default_index: int | None = None
        try:
            default = audio.get_default_input_device_info()
            default_index = int(default.get("index"))
        except Exception:
            default_index = None

        devices: list[InputDevice] = []
        for index in range(int(audio.get_device_count())):
            try:
                info = audio.get_device_info_by_index(index)
            except Exception:
                continue
            channels = int(info.get("maxInputChannels") or 0)
            if channels <= 0:
                continue
            rate = int(float(info.get("defaultSampleRate") or 0))
            devices.append(
                InputDevice(
                    index=index,
                    name=str(info.get("name") or f"input-{index}"),
                    channels=channels,
                    default_sample_rate=rate,
                    is_default=index == default_index,
                )
            )
        return devices
    finally:
        try:
            audio.terminate()
        except Exception:
            pass


def render_device_report(devices: list[InputDevice]) -> str:
    if not devices:
        return "No microphone/input devices were reported by PyAudio."

    lines = ["Available microphone/input devices:"]
    for device in devices:
        marker = " [DEFAULT]" if device.is_default else ""
        lines.append(
            f"  {device.index}: {device.name}{marker} | channels={device.channels} "
            f"| default_rate={device.default_sample_rate}Hz"
        )
    return "\n".join(lines)
