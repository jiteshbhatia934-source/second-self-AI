"""SecondSelf configuration: paths and environment variables."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    # dotenv is optional for Phase 1; provide a no-op fallback so code can run without the package installed.
    def load_dotenv(_=None):
        return

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


def _apply_streamlit_secrets() -> None:
    """Map Streamlit Cloud / secrets.toml values into os.environ (no-op outside Streamlit)."""
    try:
        import streamlit as st  # noqa: PLC0415 — optional; only available in the app runtime

        for key in (
            "GROQ_API_KEY",
            "SIMILARITY_THRESHOLD",
            "TOP_K_RETRIEVAL",
            "EMBEDDING_MODEL",
            "PUBLIC_DEMO",
            "RAW_DIR",
            "WIKI_DIR",
            "DATA_DIR",
            "GRAPH_PATH",
        ):
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


_apply_streamlit_secrets()


def _path_from_env(env_key: str, default_relative: str) -> Path:
    override = os.getenv(env_key)
    if override:
        candidate = Path(override).expanduser()
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate.resolve()
    return (PROJECT_ROOT / default_relative).resolve()


def _float_env(name: str, default: float, min_val: float, max_val: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc
    if not min_val <= value <= max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
    return value


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes")


def _int_env(name: str, default: int, min_val: int, max_val: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if not min_val <= value <= max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
    return value


RAW_DIR = _path_from_env("RAW_DIR", "raw")
WIKI_DIR = _path_from_env("WIKI_DIR", "wiki")
DATA_DIR = _path_from_env("DATA_DIR", "data")
GRAPH_PATH = _path_from_env("GRAPH_PATH", "graph.json")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
SIMILARITY_THRESHOLD = _float_env("SIMILARITY_THRESHOLD", 0.80, 0.0, 1.0)
TOP_K_RETRIEVAL = _int_env("TOP_K_RETRIEVAL", 8, 1, 20)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip()
if not EMBEDDING_MODEL:
    raise ValueError("EMBEDDING_MODEL must not be empty")

PUBLIC_DEMO = _bool_env("PUBLIC_DEMO", False)

PARA_FOLDERS = ("Projects", "Areas", "Resources", "Archives")


def ensure_project_dirs() -> None:
    """Create expected directories if they are missing."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "files").mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    for folder in PARA_FOLDERS:
        (WIKI_DIR / folder).mkdir(parents=True, exist_ok=True)


def groq_configured() -> bool:
    return bool(GROQ_API_KEY)
