#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SPEECHMATICS_API_KEY_ENV = "SPEECHMATICS_API_KEY"
VOICE_BRIDGE_TOKEN_ENV = "GUARDIAN_VOICE_BRIDGE_TOKEN"


def _guardian_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    username = os.environ.get("GUARDIAN_DEMO_USER", "")
    password = os.environ.get("GUARDIAN_DEMO_PASSWORD", "")
    if bool(username) != bool(password):
        raise RuntimeError(
            "GUARDIAN_DEMO_USER and GUARDIAN_DEMO_PASSWORD must both be set or both be unset"
        )
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"

    bridge_token = os.environ.get(VOICE_BRIDGE_TOKEN_ENV, "")
    if bridge_token:
        headers["X-Guardian-Voice-Bridge"] = bridge_token
    return headers


def _post_transcript(guardian_url: str, transcript: str) -> dict:
    payload = json.dumps(
        {
            "transcript": transcript,
            "provider": "speechmatics",
        }
    ).encode("utf-8")
    request = Request(
        guardian_url.rstrip("/") + "/api/voice/intent",
        data=payload,
        method="POST",
        headers=_guardian_headers(),
    )
    try:
        with urlopen(request, timeout=5) as response:  # nosec B310 - owner-controlled Guardian URL
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Guardian rejected voice intent: HTTP {exc.code} {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Guardian voice endpoint unavailable: {exc.reason}") from exc


async def _run_live(guardian_url: str, language: str) -> None:
    api_key = os.environ.get(SPEECHMATICS_API_KEY_ENV, "")
    if not api_key:
        raise RuntimeError(
            f"{SPEECHMATICS_API_KEY_ENV} is not configured in this runtime. "
            "Use the server-side owner-vault binding; never paste the key into Git or this script."
        )

    try:
        from speechmatics.rt import (
            AsyncClient,
            AudioEncoding,
            AudioFormat,
            AuthenticationError,
            Microphone,
            OperatingPoint,
            ServerMessageType,
            TranscriptResult,
            TranscriptionConfig,
        )
    except ImportError as exc:
        raise RuntimeError(
            "speechmatics-rt is not installed. Install the project optional dependency "
            "with: python -m pip install -e '.[speechmatics-live]'"
        ) from exc

    audio_format = AudioFormat(
        encoding=AudioEncoding.PCM_S16LE,
        chunk_size=4096,
        sample_rate=16000,
    )
    transcription_config = TranscriptionConfig(
        language=language,
        enable_partials=True,
        operating_point=OperatingPoint.ENHANCED,
    )
    microphone = Microphone(
        sample_rate=audio_format.sample_rate,
        chunk_size=audio_format.chunk_size,
    )
    if not microphone.start():
        raise RuntimeError(
            "Microphone could not start. PyAudio or the local audio device is unavailable. "
            "Guardian remains usable through the typed transcript fallback."
        )

    finals: asyncio.Queue[str] = asyncio.Queue()

    async def route_worker() -> None:
        while True:
            transcript = await finals.get()
            try:
                response = await asyncio.to_thread(_post_transcript, guardian_url, transcript)
                intent = response.get("intent", "unknown")
                truth = response.get("truth", "unknown")
                allowed = response.get("allowed", False)
                print(
                    f"[guardian] intent={intent} allowed={allowed} truth={truth} "
                    f"hash={response.get('transcript_sha256', '')[:12]}"
                )
                state = response.get("state") or {}
                current = state.get("current") or {}
                if current:
                    print(f"[guardian] state={current.get('status', 'UNKNOWN')}")
            except RuntimeError as exc:
                print(f"[guardian] {exc}", file=sys.stderr)
            finally:
                finals.task_done()

    worker = asyncio.create_task(route_worker())
    print("Speechmatics live voice bridge ready. Ctrl+C stops the microphone.")
    print("Raw audio is streamed to Speechmatics and is not written by this script.")
    print("Voice can interrupt/re-verify/resume/cancel, but it cannot approve a physical action.")

    try:
        async with AsyncClient(api_key=api_key) as client:

            @client.on(ServerMessageType.ADD_TRANSCRIPT)
            def handle_final_transcript(message: dict) -> None:
                result = TranscriptResult.from_message(message)
                transcript = result.metadata.transcript.strip()
                if transcript:
                    print(f"[speechmatics final] {transcript}")
                    finals.put_nowait(transcript)

            @client.on(ServerMessageType.ADD_PARTIAL_TRANSCRIPT)
            def handle_partial_transcript(message: dict) -> None:
                result = TranscriptResult.from_message(message)
                transcript = result.metadata.transcript.strip()
                if transcript:
                    print(f"[speechmatics partial] {transcript}")

            await client.start_session(
                transcription_config=transcription_config,
                audio_format=audio_format,
            )
            while True:
                frame = await microphone.read(audio_format.chunk_size)
                await client.send_audio(frame)
    except AuthenticationError as exc:
        raise RuntimeError("Speechmatics authentication failed") from exc
    finally:
        microphone.stop()
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream microphone audio to Speechmatics and route final transcripts into Guardian"
    )
    parser.add_argument(
        "--guardian-url",
        default=os.environ.get("GUARDIAN_DEMO_URL", "http://127.0.0.1:8787"),
        help="Guardian judge app base URL; defaults to loopback",
    )
    parser.add_argument(
        "--language",
        default=os.environ.get("GUARDIAN_SPEECH_LANGUAGE", "en"),
        help="Speechmatics language code; default en for the onsite judge demo",
    )
    args = parser.parse_args()

    try:
        asyncio.run(_run_live(args.guardian_url, args.language))
    except KeyboardInterrupt:
        print("\nSpeechmatics voice bridge stopped.")
    except RuntimeError as exc:
        print(f"Speechmatics voice bridge failed closed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
