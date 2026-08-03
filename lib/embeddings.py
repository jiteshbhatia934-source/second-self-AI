"""
lib/embeddings.py — sentence-transformers wrapper for SecondSelf.

Provides:
  load_model()            → cached SentenceTransformer (all-MiniLM-L6-v2)
  embed_text(text)        → 384-dim numpy array
  cosine_similarity(a, b) → float in [-1, 1]
  load_embeddings()       → dict from data/embeddings.pkl
  save_embeddings(obj)    → persist to data/embeddings.pkl
"""
from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
def _data_dir() -> Path:
    try:
        import config
        return config.DATA_DIR
    except Exception:
        return Path(__file__).resolve().parent.parent / "data"


def _embeddings_path() -> Path:
    return _data_dir() / "embeddings.pkl"

EMBEDDINGS_PATH = _embeddings_path()


# ── Model (module-level cache) ────────────────────────────────────────────────
_model = None
_model_name: str = "all-MiniLM-L6-v2"


def load_model(model_name: Optional[str] = None) -> Any:
    """
    Load and cache the sentence-transformers model.
    Falls back to a deterministic hash-based pseudo-embedding if the
    library is unavailable (allows tests without GPU/internet).
    """
    global _model, _model_name
    if model_name:
        _model_name = model_name
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _model = SentenceTransformer(_model_name)
    except Exception as exc:
        print(f"[embeddings] sentence-transformers unavailable ({exc}); using hash fallback.")
        _model = _HashEmbedder(_model_name)
    return _model


def embed_text(text: str, model_name: Optional[str] = None) -> np.ndarray:
    """Return a 384-dim float32 embedding vector for the given text."""
    model = load_model(model_name)
    if isinstance(model, _HashEmbedder):
        return model.encode(text)
    # sentence-transformers returns a numpy array when called with encode()
    vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return np.array(vec, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity in [-1, 1]. Returns 0.0 on zero-norm vectors."""
    if a is None or b is None:
        return 0.0
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0.0:
        return 0.0
    return float(np.dot(a, b) / norm)


def load_embeddings(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load embeddings store from disk.
    Structure:
      {
        "model": str,
        "version": 1,
        "notes": {
          slug: {"vector": np.ndarray, "hash": str, "path": str}
        }
      }
    """
    p = path or _embeddings_path()
    if not p.exists():
        return {"model": _model_name, "version": 1, "notes": {}}
    try:
        with p.open("rb") as fh:
            return pickle.load(fh)
    except Exception:
        return {"model": _model_name, "version": 1, "notes": {}}


def save_embeddings(obj: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Persist embeddings store to disk."""
    p = path or _embeddings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with tmp.open("wb") as fh:
        pickle.dump(obj, fh)
    tmp.replace(p)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _valid_vector(value: Any) -> bool:
    if not isinstance(value, np.ndarray):
        return False
    return value.shape == (384,) and np.isfinite(value).all()


def build_note_embeddings(notes: list[tuple[str, str, Path]], model_name: Optional[str] = None) -> dict[str, Any]:
    """Build or update embeddings for a set of notes.

    Notes are given as tuples of (slug, text, path). Existing embeddings are reused
    when the note text hash matches the saved hash. The returned store is saved
    to disk and includes vectors, text hashes, and the model name.
    """
    try:
        import config
        model_name = model_name or config.EMBEDDING_MODEL
    except Exception:
        model_name = model_name or _model_name

    store = load_embeddings()
    store["model"] = model_name
    store.setdefault("version", 1)
    store.setdefault("notes", {})

    for slug, text, path in notes:
        text_hash = _text_hash(text)
        existing = store["notes"].get(slug)
        if (
            existing
            and existing.get("hash") == text_hash
            and existing.get("model") == model_name
            and _valid_vector(existing.get("vector"))
        ):
            continue
        vector = embed_text(text, model_name)
        store["notes"][slug] = {
            "vector": vector,
            "hash": text_hash,
            "path": str(path),
            "model": model_name,
        }

    save_embeddings(store)
    return store


# ── Internal fallback ─────────────────────────────────────────────────────────

class _SmartTFIDFEmbedder:
    """Intelligent TF-IDF & N-gram feature hashing embedder for environments without sentence-transformers."""
    def __init__(self, name: str, dim: int = 384):
        self.name = name
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(self.dim, dtype=np.float32)

        import math
        import re
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return np.zeros(self.dim, dtype=np.float32)

        # Extract 1-grams and 2-grams for semantic n-gram matching
        ngrams = list(tokens)
        for i in range(len(tokens) - 1):
            ngrams.append(f"{tokens[i]}_{tokens[i+1]}")

        tf: dict[str, int] = {}
        for token in ngrams:
            tf[token] = tf.get(token, 0) + 1

        vec = np.zeros(self.dim, dtype=np.float32)
        for token, count in tf.items():
            # Hash token to dimension index deterministically
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dim
            # Sublinear TF weight
            weight = 1.0 + math.log(count)
            vec[h] += weight

        norm = np.linalg.norm(vec)
        if norm > 0.0:
            vec = vec / norm
        return vec.astype(np.float32)


# Keep alias for backwards compatibility
_HashEmbedder = _SmartTFIDFEmbedder
