"""
lib/llm.py — Groq API wrapper for SecondSelf.

Provides:
  call_llm(prompt, system="")   → raw string response (with retry)
  classify_content(text)         → {"para": str, "tags": list, "summary": str}
  synthesize_answer(context, question) → answer string  (used in Phase 4)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# ── Configuration ─────────────────────────────────────────────────────────────
_MODEL = "llama-3.1-8b-instant"
_MAX_RETRIES = 3
_RETRY_DELAY = 2.0   # seconds; doubled on each retry
_CLASSIFY_TEMPERATURE = 0.1
_SYNTHESIZE_TEMPERATURE = 0.3
_MAX_TOKENS = 512

_PARA_VALID = {"Projects", "Areas", "Resources", "Archives"}


def _get_client():
    """Return a Groq client, raising a clear error if key is missing."""
    try:
        from groq import Groq  # type: ignore
    except ImportError as exc:
        raise ImportError("groq package not installed. Run: pip install groq") from exc

    try:
        import streamlit as st  # type: ignore
        if "GROQ_API_KEY" in st.secrets and not os.getenv("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"])
    except Exception:
        pass

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        # Try loading from .env
        try:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parent.parent / ".env")
            api_key = os.getenv("GROQ_API_KEY", "").strip()
        except Exception:
            pass
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file or Streamlit secrets."
        )
    return Groq(api_key=api_key)





# ── Core wrapper ──────────────────────────────────────────────────────────────

def call_llm(
    prompt: str,
    system: str = "You are a helpful assistant.",
    temperature: float = _CLASSIFY_TEMPERATURE,
    max_tokens: int = _MAX_TOKENS,
) -> str:
    """
    Call the Groq API with retry + exponential backoff.
    Returns the raw text response.
    """
    client = _get_client()
    delay = _RETRY_DELAY
    last_err: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            last_err = exc
            print(
                f"[llm] Attempt {attempt}/{_MAX_RETRIES} failed: {exc}",
                file=sys.stderr,
            )
            if attempt < _MAX_RETRIES:
                time.sleep(delay)
                delay *= 2

    raise RuntimeError(f"Groq API failed after {_MAX_RETRIES} attempts: {last_err}")


# ── Classification ─────────────────────────────────────────────────────────────

_CLASSIFY_SYSTEM = """\
You are a personal knowledge organizer. Classify the given text into exactly one PARA category,
then extract tags and a one-sentence summary. Respond ONLY with valid JSON — no prose, no markdown.
JSON schema: {"para": "Projects"|"Areas"|"Resources"|"Archives", "tags": ["tag1","tag2"], "summary": "..."}
PARA definitions:
  Projects  = Has a clear goal with a deadline or active next action
  Areas     = Ongoing responsibility with no end date (health, finance, career)
  Resources = Reference material, articles, bookmarks, how-tos
  Archives  = Completed, inactive, or historical items
"""

_CLASSIFY_PROMPT_TEMPLATE = """\
Classify and summarize the following text. Respond ONLY with JSON.

TEXT:
{text}
"""


def classify_content(text: str, max_chars: int = 4000) -> Dict[str, Any]:
    """
    Call the LLM to classify text into PARA + tags + summary.
    Returns {"para": str, "tags": list[str], "summary": str}.
    Falls back gracefully on parse errors.
    """
    truncated = text[:max_chars]
    prompt = _CLASSIFY_PROMPT_TEMPLATE.format(text=truncated)

    raw = call_llm(prompt, system=_CLASSIFY_SYSTEM, temperature=_CLASSIFY_TEMPERATURE)

    # Extract JSON from response (model sometimes wraps it)
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]

    try:
        result: Dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        # Retry once with explicit JSON-only reminder
        retry_prompt = prompt + "\n\nRemember: respond ONLY with raw JSON, no markdown code fences."
        raw2 = call_llm(retry_prompt, system=_CLASSIFY_SYSTEM, temperature=0.0)
        raw2 = raw2.strip()
        s2 = raw2.find("{"); e2 = raw2.rfind("}") + 1
        try:
            result = json.loads(raw2[s2:e2]) if s2 >= 0 and e2 > s2 else {}
        except json.JSONDecodeError:
            result = {}

    # Validate and normalise
    para = str(result.get("para", "Resources")).strip()
    if para not in _PARA_VALID:
        para = "Resources"

    tags = result.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif not isinstance(tags, list):
        tags = []
    tags = [str(t).lower().strip() for t in tags][:10]

    summary = str(result.get("summary", "")).strip()[:250]

    return {"para": para, "tags": tags, "summary": summary}


# ── Synthesis (Phase 4) ────────────────────────────────────────────────────────

_SYNTHESIZE_SYSTEM = """\
You are SecondSelf, answering from the user's personal knowledge base.
Use ONLY the provided notes. If the answer isn't in the notes, say so explicitly.
Cite sources as [note-id] inline.
"""

_SYNTHESIZE_PROMPT_TEMPLATE = """\
Notes:
{context}

Question: {question}
"""


def synthesize_answer(context: str, question: str) -> str:
    """
    Generate a RAG answer from retrieved note context.
    Returns the answer string (used in Phase 4 ask.py).
    """
    prompt = _SYNTHESIZE_PROMPT_TEMPLATE.format(
        context=context[:6000],
        question=question,
    )
    return call_llm(
        prompt,
        system=_SYNTHESIZE_SYSTEM,
        temperature=_SYNTHESIZE_TEMPERATURE,
        max_tokens=800,
    )
