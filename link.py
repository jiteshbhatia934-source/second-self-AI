#!/usr/bin/env python3
"""
link.py — compute embeddings for wiki notes and auto-insert Related wikilinks

Implements Phase 3 / Sub-Phase 2.2 from implementation-plan.md

Behavior:
- Loads all wiki markdown files, parses front matter and body
- Computes or reuses embeddings (uses embeddings.py)
- Computes cosine similarity between notes
- For similarity >= SIMILARITY_THRESHOLD, ensures a link to the target appears in a Related section
- Avoids duplicate links; does not link a note to itself
- Updates front matter with embedding_version (model name stored in embeddings.pkl)

Usage:
  python link.py

"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

import config
from lib.embeddings import build_note_embeddings, EMBEDDINGS_PATH


FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def parse_markdown(path: Path) -> Tuple[Dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    meta = {}
    body = text
    if m:
        fm = m.group(1)
        body = m.group(2)
        # simple front matter parser: lines like key: 'value' or key:\n  - 'a'\n
        cur_key = None
        for line in fm.splitlines():
            if not line.strip():
                continue
            if line.startswith(" ") or line.startswith("\t"):
                # list item or continuation
                if cur_key and line.strip().startswith("-"):
                    val = line.strip().lstrip("- ").strip().strip("'\"")
                    meta.setdefault(cur_key, []).append(val)
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                if v == "":
                    meta[k] = []
                    cur_key = k
                else:
                    meta[k] = v.strip().strip("'\"")
                    cur_key = k
        # normalize tags from single string to list if needed
        if isinstance(meta.get("tags"), str):
            raw = meta.get("tags")
            # try to split on comma
            meta["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
    else:
        body = text
    return meta, body


def find_wikilinks_in_text(text: str) -> List[str]:
    return WIKILINK_RE.findall(text)


def ensure_related_section(path: Path, existing_body: str, new_links: List[str]) -> bool:
    """Ensure the Related section contains the provided wikilinks. Returns True if file changed."""
    # Normalize links to wikilink format [[slug]]
    links = [f"[[{l}]]" for l in new_links]
    body = existing_body.rstrip() + "\n"
    # Find existing Related section
    related_re = re.compile(r"(^##?\s*Related\s*$)(.*?)(^##?\s+|\Z)", re.S | re.M)
    m = related_re.search(body)
    if m:
        section = m.group(2)
        existing_links = WIKILINK_RE.findall(section)
        added = False
        for l in new_links:
            if l not in existing_links:
                section = section.rstrip() + "\n- [[%s]]\n" % l
                added = True
        if not added:
            return False
        # rebuild body
        new_body = body[: m.start(2)] + section + body[m.end(2) :]
        path.write_text(new_body, encoding="utf-8")
        return True
    else:
        # Append a Related section
        if not new_links:
            return False
        lines = ["\n## Related\n"]
        for l in new_links:
            lines.append(f"- [[{l}]]")
        new_body = body + "\n" + "\n".join(lines) + "\n"
        path.write_text(new_body, encoding="utf-8")
        return True


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def update_front_matter_embedding_version(path: Path, model_name: str) -> bool:
    """Ensure embedding_version is recorded in markdown front matter."""
    try:
        text = path.read_text(encoding="utf-8")
        m = FRONT_MATTER_RE.match(text)
        if not m:
            return False
        fm = m.group(1)
        body = m.group(2)
        if "embedding_version:" in fm:
            return False
        new_fm = fm.rstrip() + f"\nembedding_version: '{model_name}'\n"
        new_text = f"---\n{new_fm}---\n{body}"
        path.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


def main():
    config.ensure_project_dirs()
    wiki_dir = config.WIKI_DIR
    md_files = sorted(wiki_dir.rglob("*.md"))
    if not md_files:
        print(f"No wiki markdown files found in {wiki_dir}")
        return

    notes = []  # list of (slug, text, path)
    slug_map = {}  # slug -> path
    for p in md_files:
        slug = p.stem
        meta, body = parse_markdown(p)
        text = (meta.get("title", "") or slug) + "\n" + (meta.get("summary", "") or "") + "\n" + body
        notes.append((slug, text, p))
        slug_map[slug] = p

    # Build or update embeddings
    emb_store = build_note_embeddings(notes)

    # Record embedding_version in front matter
    model_name = emb_store.get("model") or config.EMBEDDING_MODEL
    for _, _, p in notes:
        update_front_matter_embedding_version(p, model_name)

    # collect vectors in same order
    slugs = [s for s, _, _ in notes]
    vectors = []
    for s in slugs:
        n = emb_store.get("notes", {}).get(s)
        if n is None:
            vectors.append(None)
        else:
            vectors.append(n["vector"])

    threshold = config.SIMILARITY_THRESHOLD
    total_added = 0
    for i, s in enumerate(slugs):
        src_vec = vectors[i]
        similarities = []
        for j, t in enumerate(slugs):
            if i == j:
                continue
            tgt_vec = vectors[j]
            sim = cosine_sim(src_vec, tgt_vec)
            if sim >= threshold:
                similarities.append((t, sim))
        # sort by descending sim
        similarities.sort(key=lambda kv: -kv[1])
        linked_slugs = [slug for slug, _ in similarities]
        if not linked_slugs:
            continue
        p = slug_map[s]
        meta, body = parse_markdown(p)
        # Avoid adding link to those already present in the file body or front matter links
        existing_links = set(find_wikilinks_in_text(body))
        if isinstance(meta.get("links"), list):
            existing_links.update(str(link) for link in meta.get("links"))
        to_add = [l for l in linked_slugs if l not in existing_links]
        if not to_add:
            continue
        changed = ensure_related_section(p, body, to_add)
        if changed:
            print(f"Updated Related for {p.name}: +{len(to_add)} links")
            total_added += len(to_add)
    # write embedding meta into embeddings.pkl (already saved by build_note_embeddings)
    if EMBEDDINGS_PATH.exists():
        print(f"Embeddings saved to {EMBEDDINGS_PATH}")
    print(f"Done. Total links added: {total_added}")


if __name__ == "__main__":
    main()

