#!/usr/bin/env python3
"""Show embeddings stored in data/embeddings.pkl."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any, Dict

import config


def load_embeddings(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {path}")
    with path.open("rb") as fh:
        return pickle.load(fh)


def format_vector(vec: Any, max_items: int = 10) -> str:
    try:
        from numpy import ndarray

        if isinstance(vec, ndarray):
            values = vec.tolist()
        else:
            values = list(vec)
    except Exception:
        values = list(vec)
    if len(values) > max_items:
        values = values[:max_items]
        return f"[{', '.join(str(x) for x in values)}... ] (length={len(vec)})"
    return f"[{', '.join(str(x) for x in values)}]"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect embeddings.pkl for SecondSelf notes")
    parser.add_argument("--slug", help="Show embedding details for a specific note slug")
    parser.add_argument("--list", action="store_true", help="List all note slugs stored in embeddings.pkl")
    parser.add_argument("--show-vector", action="store_true", help="Show the vector values for the selected slug")
    parser.add_argument("--top", type=int, default=20, help="Max number of slugs to list when using --list")
    args = parser.parse_args()

    path = config.DATA_DIR / "embeddings.pkl"
    embeddings = load_embeddings(path)

    meta = {k: v for k, v in embeddings.items() if k != "notes"}
    notes = embeddings.get("notes", {})

    print(f"Embeddings path: {path}")
    print(f"Model: {meta.get('model')}")
    print(f"Version: {meta.get('version')}")
    print(f"Total notes: {len(notes)}")
    print("")

    if args.list or not args.slug:
        print("Stored note slugs:")
        count = 0
        for slug in sorted(notes)[: args.top]:
            note = notes[slug]
            vec = note.get("vector")
            print(f"- {slug} (path={note.get('path')}, len={len(vec) if vec is not None else 0})")
            count += 1
        if args.top < len(notes):
            print(f"... and {len(notes) - args.top} more")
    if args.slug:
        slug = args.slug
        note = notes.get(slug)
        if note is None:
            matches = [s for s in notes if slug in s]
            if matches:
                print(f"Slug '{slug}' not found exactly. Partial matches:")
                for m in matches:
                    print(f"- {m}")
            else:
                print(f"Slug '{slug}' not found in embeddings.pkl")
            return
        vec = note.get("vector")
        print(f"\nDetails for slug: {slug}")
        print(f"Path: {note.get('path')}")
        print(f"Hash: {note.get('hash')}")
        print(f"Vector length: {len(vec) if vec is not None else 0}")
        if args.show_vector and vec is not None:
            print(f"Vector values: {format_vector(vec, max_items=50)}")


if __name__ == "__main__":
    main()
