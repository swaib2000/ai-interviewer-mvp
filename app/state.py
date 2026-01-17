from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class AppState:
    # -------------------
    # Config knobs (persist across reset_runtime)
    # -------------------
    region_x: int = 0
    region_y: int = 0
    region_w: int = 1280
    region_h: int = 720

    screenshot_interval_sec: float = 2.0

    # STT
    audio_chunk_seconds: float = 8.0
    stt_enabled: bool = True
    stt_provider: str = "openai"  # "openai" | "faster-whisper" | "none"
    stt_model: str = "gpt-4o-mini-transcribe"

    # Interview
    max_questions: int = 6
    auto_difficulty_ramp: bool = True

    # LLM
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.25

    # UI refresh
    live_refresh_ms: int = 1250

    # -------------------
    # Runtime/session fields (cleared by reset_runtime)
    # -------------------
    status: str = "IDLE"  # IDLE / RUNNING / PAUSED / STOPPED
    session_id: str = ""
    last_tick_ts: Optional[str] = None

    # Capture
    latest_frame_path: str = ""
    latest_frame_ts: Optional[str] = None
    latest_frame_size: Optional[Tuple[int, int]] = None  # (w,h)

    # OCR
    ocr_text: str = ""
    ocr_highlights: List[str] = field(default_factory=list)

    # STT transcript
    transcript: str = ""
    transcript_tail: str = ""

    # Q/A
    current_question: str = ""
    current_difficulty: str = "easy"
    followup_queue: List[str] = field(default_factory=list)
    qa_history: List[Dict[str, Any]] = field(default_factory=list)

    # Insights
    project_memory: str = ""
    rubric: Dict[str, float] = field(default_factory=lambda: {
        "technical_depth": 0.0,
        "clarity": 0.0,
        "originality": 0.0,
        "implementation": 0.0,
    })

    # Metrics
    ocr_calls: int = 0
    stt_calls: int = 0
    llm_calls: int = 0

    ocr_latency_ms: float = 0.0
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0

    # Log
    system_log: List[str] = field(default_factory=list)

    # Internal monotonic gates (avoid None math)
    _last_capture_monotonic: float = 0.0
    _last_stt_monotonic: float = 0.0

    # ---------------------------------------------------------
    # Logging helpers
    # ---------------------------------------------------------
    def log_info(self, msg: str) -> None:
        self.system_log.append(f"[{_now_iso()}] INFO: {msg}")

    def log_warn(self, msg: str) -> None:
        self.system_log.append(f"[{_now_iso()}] WARN: {msg}")

    def log_error(self, msg: str) -> None:
        self.system_log.append(f"[{_now_iso()}] ERROR: {msg}")

    # ---------------------------------------------------------
    # Reset helpers
    # ---------------------------------------------------------
    def reset_runtime(self) -> None:
        """Clear per-session runtime fields but keep config knobs."""
        self.status = "IDLE"
        self.session_id = ""
        self.last_tick_ts = None

        self.latest_frame_path = ""
        self.latest_frame_ts = None
        self.latest_frame_size = None

        self.ocr_text = ""
        self.ocr_highlights = []

        self.transcript = ""
        self.transcript_tail = ""

        self.current_question = ""
        self.current_difficulty = "easy"
        self.followup_queue = []
        self.qa_history = []

        self.project_memory = ""
        self.rubric = {
            "technical_depth": 0.0,
            "clarity": 0.0,
            "originality": 0.0,
            "implementation": 0.0,
        }

        self.ocr_calls = 0
        self.stt_calls = 0
        self.llm_calls = 0

        self.ocr_latency_ms = 0.0
        self.stt_latency_ms = 0.0
        self.llm_latency_ms = 0.0

        self._last_capture_monotonic = 0.0
        self._last_stt_monotonic = 0.0

        # Keep last few lines (helps debugging)
        self.system_log = self.system_log[-80:]

    def reset_all(self) -> None:
        """Clear everything including knobs."""
        fresh = AppState()
        self.__dict__.update(fresh.__dict__)

