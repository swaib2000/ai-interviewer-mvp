from __future__ import annotations

import os
import time
from typing import Tuple


def _has_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_question(
    *,
    model: str,
    temperature: float,
    ocr_context: str,
    difficulty: str,
    question_index: int,
    max_questions: int,
) -> Tuple[str, float, str]:
    """
    Returns (question, latency_ms, error_message)
    error_message is "" on success.
    """
    if not _has_key():
        return "", 0.0, "OPENAI_API_KEY not set"

    t0 = time.time()
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI()

        system = (
            "You are an AI interviewer for a software/ML project demo. "
            "Generate ONE concise interview question based on on-screen context. "
            "No bullet lists. No multiple questions."
        )

        user = (
            f"Difficulty: {difficulty}\n"
            f"Question {question_index}/{max_questions}\n\n"
            f"On-screen OCR context (may be noisy):\n{ocr_context}\n\n"
            "Ask ONE question that tests architecture + implementation detail."
        )

        resp = client.chat.completions.create(
            model=model,
            temperature=float(temperature),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        q = (resp.choices[0].message.content or "").strip()
        ms = (time.time() - t0) * 1000.0
        return q, ms, ""
    except Exception as e:
        ms = (time.time() - t0) * 1000.0
        return "", ms, f"{type(e).__name__}: {e}"

