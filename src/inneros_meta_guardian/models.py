"""Local-first reasoning adapter. LLM narration is NOT an authority to actuate devices."""
from __future__ import annotations

import json
import os
from urllib.parse import urlsplit
import urllib.error
import urllib.request

SYSTEM = (
    "You are a careful physical-infrastructure incident analyst. The input is SYNTHETIC "
    "training/demo telemetry, not a real event. Explain the likely cause and a safe next step "
    "in fewer than 90 words. Do not create new observations, commands, device identities, "
    "credentials, certainty claims, or approval. Only deterministic policy can authorize an action."
)


class ModelUnavailable(Exception):
    """Provider is missing, disabled, unreachable or returned a malformed response."""


def _post(url: str, payload: dict, headers: dict, timeout: float = 8.0) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(65536)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON response must be an object")
        return data
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        # Do not surface remote error bodies or Authorization headers to clients or audit.
        raise ModelUnavailable(f"Inference provider unavailable ({type(exc).__name__}).") from None


def _extract_meta(data: dict) -> str:
    # Official Meta Model API Responses API: output[].type=message, content[].type=output_text.
    try:
        output = data["output"]
        messages = [x for x in output if x.get("type") == "message"]
        content = [c.get("text", "") for m in messages for c in m.get("content", []) if c.get("type") == "output_text"]
        result = " ".join(content).strip()
        if result:
            return result[:1200]
    except (KeyError, TypeError, AttributeError):
        pass
    raise ModelUnavailable("Unexpected Meta Responses API payload.")


def _local_url() -> str:
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1") or parsed.username or parsed.password or parsed.path != "/api/chat":
        raise ModelUnavailable("Ollama endpoint must be loopback HTTP /api/chat.")
    return url


def narrate(mode: str, incident: dict) -> dict:
    if mode == "deterministic":
        return {"provider": "deterministic", "model": "local-rule-engine", "live_model": False,
                "narrative": incident["explanation"], "truth": "DETERMINISTIC_RULE"}

    compact = {"title": incident["title"], "signals": incident["signals"],
               "site": incident["site"], "severity": incident["severity"]}
    prompt = json.dumps(compact, ensure_ascii=False)

    if mode == "meta":
        if os.getenv("ALLOW_EXTERNAL_META", "false").lower() != "true":
            raise ModelUnavailable("Meta is disabled; ALLOW_EXTERNAL_META=true is required.")
        key = os.getenv("MODEL_API_KEY", "")
        if not key:
            raise ModelUnavailable("MODEL_API_KEY is not configured.")
        base = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
        if base != "https://api.meta.ai/v1":
            raise ModelUnavailable("Meta endpoint must be the official https://api.meta.ai/v1.")
        model = os.getenv("META_MODEL", "muse-spark-1.3")
        data = _post(
            f"{base}/responses",
            {"model": model, "instructions": SYSTEM, "input": prompt, "max_output_tokens": 256, "store": False},
            {"Authorization": f"Bearer {key}"},
        )
        return {"provider": "meta", "model": model, "live_model": True,
                "narrative": _extract_meta(data), "truth": "MODEL_GENERATED_FROM_SIMULATED_SIGNALS"}

    if mode == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        response = _post(
            _local_url(),
            {"model": model,
             "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
             "stream": False},
            {},
        )
        try:
            result = str(response["message"]["content"]).strip()[:1200]
        except (KeyError, TypeError):
            raise ModelUnavailable("Unexpected local inference payload.") from None
        if not result:
            raise ModelUnavailable("Ollama returned empty output.")
        return {"provider": "ollama", "model": model, "live_model": True,
                "narrative": result, "truth": "LOCAL_MODEL_FROM_SIMULATED_SIGNALS"}
    raise ValueError("Invalid inference mode")
