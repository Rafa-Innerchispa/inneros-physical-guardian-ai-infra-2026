from __future__ import annotations

import hashlib
import importlib.util
import os
import re
from typing import Any

SPEECHMATICS_API_KEY_ENV = "SPEECHMATICS_API_KEY"

# Voice is deliberately not an approval surface. These terms are evaluated before
# any bounded operational intent so a phrase such as "approve and resume" cannot
# accidentally fall through to resume.
_DENIED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("approve_action", re.compile(r"\b(approve|authorize|authorise|autoriz(?:a|ar|e)|aprobar|aprueba)\b", re.I)),
    ("execute_action", re.compile(r"\b(execute|ejecut(?:a|ar|e)|run the action|do it)\b", re.I)),
    ("unlock_access", re.compile(r"\b(unlock|open (?:the )?(?:door|gate)|abrir? (?:la )?(?:puerta|porton|portón))\b", re.I)),
    ("disable_safety", re.compile(r"\b(disable (?:the )?(?:alarm|safety)|desactiv(?:a|ar|e) (?:la )?alarma)\b", re.I)),
)

_INTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "explain_trigger",
        re.compile(
            r"\b(explain|why|what triggered|que paso|qué pasó|explica|por que|por qué).*(trigger|incident|evento|incidente|reason|razon|razón)?\b",
            re.I,
        ),
    ),
    (
        "show_camera",
        re.compile(r"\b(show|display|camera|camara|cámara|muestra|mostrar)\b(?:\s+camera|\s+camara|\s+cámara)?\s*(?P<camera>\d+)?", re.I),
    ),
    (
        "acknowledge_incident",
        re.compile(r"\b(acknowledge|ack|confirm incident|reconozco|reconocer|acknowledge incident|confirmar incidente)\b", re.I),
    ),
    (
        "interrupt_action",
        re.compile(r"\b(interrupt|stop action|stop the action|halt|interrumpe|interrumpir|deten|detén|detener)\b", re.I),
    ),
    (
        "reverify_safe_state",
        re.compile(r"\b(re[- ]?verify|verify safe state|reverifica|reverificar|verifica estado seguro|verificar estado seguro)\b", re.I),
    ),
    (
        "resume_action",
        re.compile(r"\b(resume|continue action|continue the action|reanuda|reanudar|continua accion|continúa acción|continuar accion|continuar acción)\b", re.I),
    ),
    (
        "cancel_action",
        re.compile(r"\b(cancel|cancel action|cancelar|cancela|aborta|abortar)\b", re.I),
    ),
)


def speechmatics_status() -> dict[str, Any]:
    """Return readiness without exposing credential material."""
    return {
        "provider": "speechmatics",
        "credential_configured": bool(os.environ.get(SPEECHMATICS_API_KEY_ENV)),
        "sdk_installed": importlib.util.find_spec("speechmatics") is not None,
        "api_key_env": SPEECHMATICS_API_KEY_ENV,
        "raw_audio_persisted": False,
        "voice_can_approve": False,
        "truth_policy": {
            "http_transcript": "CLIENT_REPORTED_TRANSCRIPT",
            "live_sdk": "SPEECHMATICS_LIVE_TRANSCRIPT",
        },
    }


def _transcript_hash(transcript: str) -> str:
    return hashlib.sha256(transcript.encode("utf-8")).hexdigest()


def _normalized(transcript: str) -> str:
    return " ".join(transcript.strip().split())


def classify_voice_intent(transcript: str) -> dict[str, Any]:
    text = _normalized(transcript)
    if not text:
        raise ValueError("transcript is required")
    if len(text) > 2_000:
        raise ValueError("transcript is too long")

    for reason, pattern in _DENIED_PATTERNS:
        if pattern.search(text):
            return {
                "intent": "denied_voice_action",
                "allowed": False,
                "reason": reason,
            }

    for intent, pattern in _INTENT_PATTERNS:
        match = pattern.search(text)
        if match:
            result: dict[str, Any] = {"intent": intent, "allowed": True}
            if intent == "show_camera":
                camera = match.groupdict().get("camera")
                result["camera"] = int(camera) if camera else None
            return result

    return {
        "intent": "unknown",
        "allowed": False,
        "reason": "no_bounded_intent_match",
    }


class GuardianVoiceRouter:
    """Bounded voice adapter around an existing Guardian demo engine.

    Speech-to-text is an input transport only. Human approval remains on the
    explicit Guardian approval surface and cannot be granted by voice.
    """

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def route(
        self,
        transcript: str,
        *,
        provider: str = "speechmatics",
        source_truth: str = "CLIENT_REPORTED_TRANSCRIPT",
    ) -> dict[str, Any]:
        text = _normalized(transcript)
        classified = classify_voice_intent(text)
        base: dict[str, Any] = {
            "ok": bool(classified["allowed"]),
            "provider": provider,
            "intent": classified["intent"],
            "allowed": classified["allowed"],
            "transcript_sha256": _transcript_hash(text),
            "transcript_persisted": False,
            "raw_audio_persisted": False,
            "truth": source_truth,
            "voice_can_approve": False,
        }

        if not classified["allowed"]:
            base.update(
                {
                    "fail_closed": True,
                    "reason": classified.get("reason", "voice intent denied"),
                    "state": self.engine.state(),
                }
            )
            return base

        intent = classified["intent"]
        if intent == "explain_trigger":
            current = self.engine.state().get("current")
            if not current:
                raise RuntimeError("no active incident to explain")
            decide_stage = next(
                (stage for stage in current.get("stages", []) if stage.get("stage") == "DECIDE"),
                {},
            )
            base["explanation"] = {
                "scenario": current.get("scenario"),
                "summary": decide_stage.get("summary", "Guardian has an active incident"),
                "reason_codes": decide_stage.get("reason_codes", []),
                "status": current.get("status"),
            }
            base["state"] = self.engine.state()
            return base

        if intent == "show_camera":
            # The hackathon UI currently renders one bounded camera/sensor stage.
            # We return a navigation request instead of inventing access to a camera.
            base["camera_request"] = {
                "camera": classified.get("camera"),
                "status": "UI_NAVIGATION_ONLY",
            }
            base["state"] = self.engine.state()
            return base

        if intent == "acknowledge_incident":
            if not self.engine.state().get("current"):
                raise RuntimeError("no active incident to acknowledge")
            base["acknowledgement"] = "RECORDED_IN_VOICE_RESPONSE_ONLY"
            base["state"] = self.engine.state()
            return base

        if intent == "interrupt_action":
            base["state"] = self.engine.interrupt()
            return base
        if intent == "reverify_safe_state":
            base["state"] = self.engine.reverify()
            return base
        if intent == "resume_action":
            # Engine.resume() is the canonical fail-closed reverification gate.
            base["state"] = self.engine.resume()
            return base
        if intent == "cancel_action":
            base["state"] = self.engine.cancel()
            return base

        raise RuntimeError(f"unsupported bounded voice intent: {intent}")
