"""
generate_index.py — build data/index.json summarizing wiki notes and embedding presence
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import config
from embeddings import load_embeddings, EMBEDDINGS_PATH

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)


def parse_front_matter(text: str):
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    fm = m.group(1)
    body = m.group(2)
    meta = {}
    cur_key = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") or line.startswith("\t"):
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
    return meta, body


def main():
    config.ensure_project_dirs()
    wiki = config.WIKI_DIR
    md_files = sorted(wiki.rglob("*.md"))
    emb_store = load_embeddings(EMBEDDINGS_PATH)
    notes = []
    for p in md_files:
        text = p.read_text(encoding='utf-8')
        meta, body = parse_front_matter(text)
        slug = p.stem
        has_emb = slug in emb_store.get('notes', {})
        notes.append({
            'slug': slug,
            'title': meta.get('title') or slug,
            'para': meta.get('para') or '',
            'tags': meta.get('tags') or [],
            'summary': meta.get('summary') or '',
            'path': str(p),
            'has_embedding': bool(has_emb)
        })
    out = {
        'meta': {
            'count': len(notes),
            'embeddings_path': str(EMBEDDINGS_PATH) if EMBEDDINGS_PATH.exists() else None,
        },
        'notes': notes
    }
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = config.DATA_DIR / 'index.json'
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Wrote {target} with {len(notes)} notes")

if __name__ == '__main__':
    main()
