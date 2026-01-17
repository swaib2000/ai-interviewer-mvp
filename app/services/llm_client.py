import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

def generate_llm_question(context: str) -> str:
    prompt = f"""
You are an AI interviewer.

Based on the following project context, ask ONE clear technical interview question.
Do not explain. Ask only the question.

Context:
{context}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        t0 = time.time()
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        return f"[LLM ERROR] {e}"

