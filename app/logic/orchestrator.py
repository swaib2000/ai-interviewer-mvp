from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from app.state import AppState
from app.capture.screen import capture_screen
from app.services.stt import transcribe_audio_bytes

# If you have OCR service, keep it. Otherwise it will be caught safely.
try:
    from app.services.ocr import run_ocr  # type: ignore
except Exception:
    run_ocr = None  # type: ignore

from app.logic.llm_interviewer import generate_question


ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LATEST_FRAME = ASSETS_DIR / "latest_frame.png"


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _next_difficulty(state: AppState) -> str:
    if not state.auto_difficulty_ramp:
        return state.current_difficulty or "easy"

    n = len(state.qa_history)
    if n < 2:
        return "easy"
    if n < 4:
        return "medium"
    return "hard"


def start_session(state: AppState) -> None:
    state.reset_runtime()
    state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    state.status = "RUNNING"
    state.log_info("Session started.")


def pause_resume(state: AppState) -> None:
    if state.status == "RUNNING":
        state.status = "PAUSED"
        state.log_info("Session paused.")
    elif state.status == "PAUSED":
        state.status = "RUNNING"
        state.log_info("Session resumed.")


def stop_session(state: AppState) -> None:
    state.status = "STOPPED"
    state.log_info("Session stopped.")


def clear_state(state: AppState) -> None:
    state.reset_runtime()
    state.log_info("Cleared runtime state.")


def process_uploaded_audio(state: AppState, audio_bytes: bytes, filename: str) -> None:
    """Manual STT: upload audio -> transcribe -> append transcript."""
    if not audio_bytes:
        state.log_warn("No audio bytes provided.")
        return

    if not state.stt_enabled:
        state.log_warn("STT disabled in settings.")
        return

    text, ms, err = transcribe_audio_bytes(
        audio_bytes,
        filename=filename,
        provider=state.stt_provider,
        model=state.stt_model,
    )

    if err:
        state.log_error(f"STT failed: {err}")
        return

    state.stt_calls += 1
    state.stt_latency_ms = ms

    if text:
        # append to transcript
        if state.transcript:
            state.transcript += "\n"
        state.transcript += text
        state.transcript_tail = state.transcript[-800:]
        state.log_info(f"STT ok ({ms:.1f} ms): +{len(text)} chars")
    else:
        state.log_warn("STT returned empty text.")


def tick(state: AppState) -> None:
    """
    Called every Streamlit rerun.
    - Captures screen periodically (when RUNNING)
    - Runs OCR (if available)
    - Generates a question (LLM) when needed
    """
    state.last_tick_ts = _now_iso()

    if state.status != "RUNNING":
        return

    # -------------------
    # Capture throttling (monotonic)
    # -------------------
    interval = float(state.screenshot_interval_sec or 2.0)
    now_m = time.monotonic()

    if (now_m - float(state._last_capture_monotonic or 0.0)) < interval:
        return

    state._last_capture_monotonic = now_m

    # -------------------
    # Capture screenshot
    # -------------------
    try:
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        out_path, (w, h) = capture_screen(
            str(LATEST_FRAME),
            region=(state.region_x, state.region_y, state.region_w, state.region_h),
        )
        state.latest_frame_path = out_path
        state.latest_frame_ts = _now_iso()
        state.latest_frame_size = (w, h)
        state.log_info(f"Captured frame: {out_path} size=({w},{h})")
    except Exception as e:
        state.log_error(f"capture_screen failed: {type(e).__name__}: {e}")
        return

    # -------------------
    # OCR (optional)
    # -------------------
    if run_ocr is not None:
        try:
            text, ms = run_ocr(state.latest_frame_path)
            state.ocr_calls += 1
            state.ocr_latency_ms = float(ms)
            state.ocr_text = text or ""

            hl = []
            for line in (state.ocr_text or "").splitlines():
                line = line.strip()
                if len(line) >= 6:
                    hl.append(line[:120])
                if len(hl) >= 6:
                    break
            state.ocr_highlights = hl

        except Exception as e:
            state.log_warn(f"OCR failed: {type(e).__name__}: {e}")
    else:
        state.ocr_highlights = ["(OCR unavailable)"]

    # -------------------
    # LLM question generation
    # -------------------
    if not state.current_question and len(state.qa_history) < int(state.max_questions):
        difficulty = _next_difficulty(state)
        q_index = len(state.qa_history) + 1

        q, ms, err = generate_question(
            model=state.llm_model,
            temperature=state.llm_temperature,
            ocr_context=state.ocr_text or "",
            difficulty=difficulty,
            question_index=q_index,
            max_questions=int(state.max_questions),
        )

        if err:
            state.log_error(f"LLM failed ({err})")
            q = "Can you briefly explain the overall architecture of this project (modules + data flow)?"
            state.log_warn("Used fallback question.")
        else:
            state.llm_calls += 1
            state.llm_latency_ms = ms

        state.current_difficulty = difficulty
        state.current_question = q
        state.followup_queue = ["What’s one concrete implementation detail you’re proud of?"]

