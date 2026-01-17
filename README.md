# AI-Driven Automated Interviewer for Project Presentations

<img width="1441" height="752" alt="image" src="https://github.com/user-attachments/assets/3505c779-209e-4fc5-a09a-ce52ec39c1cc" />

An AI-powered system that **observes a student’s live project presentation**, understands on-screen content, and **conducts an adaptive technical interview** in real time.
The system integrates **screen capture, OCR-based context extraction, LLM-driven question generation, session orchestration, and a live dashboard**, making it suitable for hackathons, interviews, and academic demos.

<img width="1600" height="862" alt="image" src="https://github.com/user-attachments/assets/49e53b71-07fe-4cac-93d8-641b8707122f" />



## 🚀 Key Features

- 🖥 **Live Screen Capture**
  - Periodically captures a selected region of the presenter’s screen.
- 🔍 **On-Screen Content Understanding**
  - Extracts textual context from the screen using OCR (when enabled).
- 🤖 **AI Interviewer**
  - Generates context-aware technical questions using a Large Language Model (LLM).
  - Automatically ramps question difficulty across the session.
- 🧠 **Session Orchestration**
  - Handles start / pause / resume / stop lifecycle reliably.
- 📊 **Interactive Dashboard**
  - Displays screen snapshot, OCR highlights, interview questions, transcript, logs, and metrics.
- 🧩 **Extensible Architecture**
  - Speech-to-Text (STT), scoring, and report generation can be added cleanly.

---

## 🧱 High-Level Architecture
```text
┌──────────────┐
│  Screen UI   │  ← Streamlit dashboard
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│  Orchestrator       │
│  (control loop)     │
└──────┬──────┬───────┘
       │      │
       ▼      ▼
    Screen  LLM Interviewer
    Capture  (Question Gen)
       │
       ▼
     OCR

```
---

## 📁 Project Structure

```text
ai-interviewer-mvp/
│
├── app/
│   ├── main.py                # Streamlit entry point (UI + dashboard)
│   ├── state.py               # Central application state (single source of truth)
│   │
│   ├── logic/
│   │   ├── orchestrator.py    # Control loop (session lifecycle, timing, routing)
│   │   └── llm_interviewer.py # LLM-based question generation
│   │
│   ├── capture/
│   │   └── screen.py          # Screen capture utilities (live snapshots)
│   │
│   └── assets/                # Runtime-generated artifacts (gitignored)
│       └── latest_frame.png
│
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
└── .gitignore                 # Git ignore rules
```



---

## 📄 File-by-File Explanation

### `app/main.py` — **Streamlit UI & Entry Point**
- Entry point of the application.
- Defines the dashboard layout:
  - Live screen snapshot
  - OCR highlights
  - Current interview question
  - Transcript and metrics
  - System logs
- Provides session controls:
  - Start / Pause / Resume / Stop / Clear
- Triggers the orchestrator loop on every Streamlit rerun.

---

### `app/state.py` — **Central State Management**
- Defines the `AppState` dataclass.
- Acts as the **single source of truth** for:
  - Session status
  - Screen capture metadata
  - OCR text and highlights
  - Transcript
  - Interview questions and difficulty
  - Metrics (OCR calls, LLM calls, latency)
  - System logs
- Ensures clean separation between UI and logic.

---

### `app/logic/orchestrator.py` — **System Orchestration**
- Core control loop of the system.
- Responsibilities:
  - Session lifecycle management
  - Periodic screen capture
  - OCR invocation
  - LLM question generation
  - Throttling, timing, and state updates
- Designed as a safe, tick-based loop compatible with Streamlit.

---

### `app/logic/llm_interviewer.py` — **AI Question Generator**
- Handles all LLM interactions.
- Uses OCR context and session state to generate:
  - A single, focused technical interview question at a time.
- Uses OpenAI APIs with graceful fallback if quota or API key is unavailable.

---

### `app/capture/screen.py` — **Screen Capture Utility**
- Captures the full screen or a specified region.
- Uses OS-native screen capture for reliability.
- Writes images atomically to prevent corrupted reads.
- Returns image path and dimensions for UI rendering.

---

### `app/assets/` — **Runtime Artifacts (Ignored by Git)**
- Stores temporary files such as:
  - Latest screenshots
  - Audio files (future STT)
- Automatically created at runtime.
- Excluded via `.gitignore`.

---

## ⚙️ Installation & Setup

### 1 Clone the Repository
```bash
git clone https://github.com/swaib2000/ai-interviewer-mvp.git
cd ai-interviewer-mvp 
```
### 2 Create & Activate Virtual Environment (Recommended)
python3 -m venv venv
source venv/bin/activate

### 3 Install Dependencies
pip install -r requirements.txt

### 4 Set Environment Variables
Set your OpenAI API key (required for LLM question generation):
export OPENAI_API_KEY="your_openai_api_key"

### 5 Run the Application
PYTHONPATH=. streamlit run app/main.py

// The Streamlit dashboard will open in your browser.



