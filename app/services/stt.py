from __future__ import annotations

import os
import time
from typing import Tuple


def transcribe_audio_bytes(
    audio_bytes: bytes,
    *,
    filename: str = "audio.wav",
    provider: str = "openai",
    model: str = "gpt-4o-mini-transcribe",
) -> Tuple[str, float, str]:
    """
    Returns (text, latency_ms, error_message)
    provider: "openai" | "faster-whisper" | "none"
    """
    t0 = time.time()

    if provider == "none":
        return "", 0.0, "STT provider disabled"

    # --- OpenAI STT ---
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            return "", 0.0, "OPENAI_API_KEY not set"

        try:
            from openai import OpenAI  # type: ignore
            import io

            client = OpenAI()
            f = io.BytesIO(audio_bytes)
            f.name = filename  # important: OpenAI uses file name extension sometimes

            # Newer OpenAI SDK supports `audio.transcriptions.create`
            resp = client.audio.transcriptions.create(
                model=model,
                file=f,
            )
            text = (resp.text or "").strip()  # type: ignore
            ms = (time.time() - t0) * 1000.0
            return text, ms, ""

        except Exception as e:
            ms = (time.time() - t0) * 1000.0
            return "", ms, f"{type(e).__name__}: {e}"

    # --- faster-whisper (local) ---
    if provider == "faster-whisper":
        try:
            from faster_whisper import WhisperModel  # type: ignore
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()

                wm = WhisperModel("small", device="auto", compute_type="auto")
                segments, _info = wm.transcribe(tmp.name)
                text = " ".join(seg.text.strip() for seg in segments).strip()

            ms = (time.time() - t0) * 1000.0
            return text, ms, ""

        except Exception as e:
            ms = (time.time() - t0) * 1000.0
            return "", ms, f"{type(e).__name__}: {e}"

    return "", (time.time() - t0) * 1000.0, f"Unknown STT provider: {provider}"

