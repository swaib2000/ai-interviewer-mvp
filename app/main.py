from __future__ import annotations

import streamlit as st

from app.state import AppState
from app.logic.orchestrator import (
    start_session,
    pause_resume,
    stop_session,
    clear_state,
    tick,
    process_uploaded_audio,
)


def _get_state() -> AppState:
    if "APP_STATE" not in st.session_state:
        st.session_state["APP_STATE"] = AppState()
    return st.session_state["APP_STATE"]


st.set_page_config(page_title="AI Project Interviewer (Live)", layout="wide")
S = _get_state()

# -------------------------
# Sidebar controls
# -------------------------
with st.sidebar:
    st.markdown("## Controls")

    st.markdown("### Capture")
    S.region_x = int(st.number_input("Region X", value=int(S.region_x), step=10))
    S.region_y = int(st.number_input("Region Y", value=int(S.region_y), step=10))
    S.region_w = int(st.number_input("Region W", value=int(S.region_w), step=10))
    S.region_h = int(st.number_input("Region H", value=int(S.region_h), step=10))
    S.screenshot_interval_sec = float(st.slider("Screenshot interval (sec)", 0.5, 10.0, float(S.screenshot_interval_sec), 0.5))

    st.markdown("### Interview")
    S.max_questions = int(st.slider("Max questions", 1, 20, int(S.max_questions), 1))
    S.auto_difficulty_ramp = bool(st.checkbox("Auto difficulty ramp", value=bool(S.auto_difficulty_ramp)))

    st.markdown("### LLM")
    S.llm_model = st.text_input("LLM model", value=S.llm_model)
    S.llm_temperature = float(st.slider("LLM temperature", 0.0, 1.0, float(S.llm_temperature), 0.05))

    st.markdown("### STT (Speech-to-Text)")
    S.stt_enabled = bool(st.checkbox("Enable STT", value=bool(S.stt_enabled)))
    S.stt_provider = st.selectbox("STT provider", ["openai", "faster-whisper", "none"], index=["openai","faster-whisper","none"].index(S.stt_provider))
    S.stt_model = st.text_input("STT model (OpenAI)", value=S.stt_model)

    uploaded_audio = st.file_uploader("Upload audio (wav/mp3/m4a)", type=["wav", "mp3", "m4a"])
    if uploaded_audio is not None and st.button("Transcribe uploaded audio", use_container_width=True):
        process_uploaded_audio(S, uploaded_audio.read(), uploaded_audio.name)

    st.markdown("### Live loop")
    S.live_refresh_ms = int(st.slider("Refresh interval (ms)", 200, 3000, int(S.live_refresh_ms), 50))

# -------------------------
# Header + buttons
# -------------------------
colA, colB = st.columns([3, 2])
with colA:
    st.title("AI Project Interviewer (Live)")
with colB:
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Start Session", use_container_width=True):
            start_session(S)
    with b2:
        if st.button("Pause / Resume", use_container_width=True):
            pause_resume(S)
    with b3:
        if st.button("Stop Session", use_container_width=True):
            stop_session(S)
    with b4:
        if st.button("Clear State", use_container_width=True):
            clear_state(S)

status_icon = {"IDLE": "⚪", "RUNNING": "🟢", "PAUSED": "🟡", "STOPPED": "🔴"}.get(S.status, "⚪")
st.caption(f"{status_icon} **{S.status}**")

# One tick per rerun
tick(S)

# -------------------------
# Main layout
# -------------------------
c1, c2, c3 = st.columns([1.2, 1.2, 1.0])

with c1:
    st.subheader("Live Inputs")
    st.markdown("**Live Screen Snapshot**")
    if S.latest_frame_path:
        try:
            st.image(S.latest_frame_path, caption=f"Last frame: {S.latest_frame_ts}", use_container_width=True)
        except Exception as e:
            S.log_warn(f"st.image failed for {S.latest_frame_path}: {type(e).__name__}: {e}")
            st.warning("Latest screenshot file is not a valid image yet (permission/empty file). Check System Log.")
    else:
        st.info("No valid frame yet.")

    st.markdown("---")
    st.markdown("**OCR Extract (deduped highlights)**")
    if S.ocr_highlights:
        for h in S.ocr_highlights:
            st.write(f"- {h}")
    else:
        st.write("—")
    st.caption(f"OCR calls: {S.ocr_calls} | OCR latency (last): {S.ocr_latency_ms:.1f} ms")

with c2:
    st.subheader("Conversation")
    st.markdown("**Live Transcript**")
    st.write(S.transcript_tail or "—")
    st.caption(f"STT calls: {S.stt_calls} | STT latency (last): {S.stt_latency_ms:.1f} ms")

    st.markdown("---")
    st.markdown("**Current Question**")
    if S.current_question:
        st.markdown(f"**Q{len(S.qa_history) + 1} ·** `{S.current_difficulty}`")
        st.write(S.current_question)
    else:
        st.info("No question yet.")

    if S.followup_queue:
        with st.expander("Follow-up (queued)", expanded=False):
            for f in S.followup_queue:
                st.write(f"- {f}")

with c3:
    st.subheader("Insights")
    st.markdown("**Project Memory (LLM-updated)**")
    st.write(S.project_memory or "—")

    st.markdown("---")
    st.markdown("**Running Rubric (0–5)**")
    for k in ["technical_depth", "clarity", "originality", "implementation"]:
        v = float(S.rubric.get(k, 0.0))
        st.progress(min(max(v / 5.0, 0.0), 1.0), text=f"{k.replace('_',' ').title()}: {v:.1f}/5")

    st.markdown("---")
    st.markdown("**System Metrics**")
    st.json({
        "session_id": S.session_id,
        "status": S.status,
        "last_tick_ts": S.last_tick_ts,
        "latest_frame_ts": S.latest_frame_ts,
        "latest_frame_path": S.latest_frame_path,
        "ocr_calls": S.ocr_calls,
        "stt_calls": S.stt_calls,
        "llm_calls": S.llm_calls,
        "llm_model": S.llm_model,
        "stt_provider": S.stt_provider,
    })

st.markdown("---")
with st.expander("System Log", expanded=True):
    st.text("\n".join(S.system_log[-200:]) if S.system_log else "—")

# Dependency-free "live" refresh when RUNNING
if S.status == "RUNNING":
    st.caption(f"Auto-refresh every {S.live_refresh_ms} ms while RUNNING…")
    import time
    time.sleep(S.live_refresh_ms / 1000.0)
    st.rerun()

