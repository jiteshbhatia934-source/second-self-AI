"""
embeddings.py — helper for computing and caching note embeddings

Provides a fallback embedding method when sentence-transformers isn't available.
Persists embeddings to data/embeddings.pkl with structure:
{
  "model": <model_name>,
  "version": 1,
  "notes": {
      "slug": {"vector": np.ndarray, "hash": <sha1>, "path": <md path>}
  }
}

"""
from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np

import config


EMBEDDINGS_PATH = config.DATA_DIR / "embeddings.pkl"


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def load_embeddings(path: Path = EMBEDDINGS_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {"model": None, "version": 1, "notes": {}}
    try:
        with path.open("rb") as fh:
            return pickle.load(fh)
    except Exception:
        return {"model": None, "version": 1, "notes": {}}


def save_embeddings(obj: Dict[str, Any], path: Path = EMBEDDINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pickle.dump(obj, fh)


def _hash_to_vector(h: str, dim: int = 384) -> np.ndarray:
    # Convert hex hash into a deterministic pseudo-embedding vector
    # Repeat SHA256 to get enough bytes
    b = hashlib.sha256(h.encode("utf-8")).digest()
    # Expand to dim bytes by repeated hashing
    out = bytearray()
    seed = b
    while len(out) < dim * 4:
        seed = hashlib.sha256(seed).digest()
        out.extend(seed)
    # interpret as floats in [-1,1]
    arr = np.frombuffer(bytes(out[: dim * 4]), dtype=np.uint32).astype(np.float32)
    arr = (arr % 100000) / 100000.0  # normalize to 0..1
    arr = (arr - 0.5) * 2.0  # scale to -1..1
    # if longer, truncate
    if arr.size > dim:
        arr = arr[:dim]
    # if shorter, pad zeros
    if arr.size < dim:
        pad = np.zeros(dim - arr.size, dtype=np.float32)
        arr = np.concatenate([arr, pad])
    # L2 normalize
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr


def embed_texts(texts: List[str], model_name: str = config.EMBEDDING_MODEL) -> List[np.ndarray]:
    """
    Try to use sentence-transformers; if unavailable, fall back to deterministic hash-based vectors.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer(model_name)
        embs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        # ensure 2D numpy array
        return [embs[i].astype("float32") for i in range(len(texts))]
    except Exception:
        # Fallback: deterministic hash-based embeddings
        print("Warning: sentence-transformers unavailable — using deterministic fallback embeddings.")
        out = []
        for t in texts:
            h = _sha1(t)
            v = _hash_to_vector(h, dim=384)
            out.append(v.astype("float32"))
        return out


def build_note_embeddings(notes: List[Tuple[str, str, Path]]) -> Dict[str, Any]:
    """
    notes: list of tuples (slug, text, path)
    returns embeddings object suitable for save_embeddings
    """
    emb_store = load_embeddings()
    changed = False
    texts = []
    slugs = []
    # determine which need recompute
    to_compute = []
    for slug, text, path in notes:
        content_hash = _sha1(text)
        existing = emb_store.get("notes", {}).get(slug)
        if existing and existing.get("hash") == content_hash and emb_store.get("model") == config.EMBEDDING_MODEL:
            # reuse
            continue
        slugs.append(slug)
        texts.append(text)
        to_compute.append((slug, content_hash, path))

    if texts:
        vectors = embed_texts(texts, model_name=config.EMBEDDING_MODEL)
        for (slug, content_hash, path), vec in zip(to_compute, vectors):
            emb_store.setdefault("notes", {})[slug] = {
                "vector": vec,
                "hash": content_hash,
                "path": str(path),
            }
            changed = True
    # record model
    if emb_store.get("model") != config.EMBEDDING_MODEL:
        emb_store["model"] = config.EMBEDDING_MODEL
        changed = True
    if changed:
        save_embeddings(emb_store)
    return emb_store


def get_vectors_for_slugs(emb_store: Dict[str, Any], slugs: List[str]) -> List[np.ndarray]:
    out = []
    for s in slugs:
        note = emb_store.get("notes", {}).get(s)
        if note is None:
            out.append(None)
        else:
            out.append(note["vector"])
    return out
