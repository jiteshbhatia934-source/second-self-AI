#!/usr/bin/env python3
"""
classify.py — simple local classifier for Phase 2.1 (Sorting Hat)

Scans raw/*.json and creates wiki/{Para}/{slug}.md with YAML front matter:
- id: uuid4
- raw_id: <raw filename id>
- para: Projects|Areas|Resources|Archives
- tags: [..]
- summary: short text
- title: derived title
- created_at, classified_at

If GROQ_API_KEY is set in config.py the script logs that remote classification is possible but still uses local heuristics as a safe default.

Usage:
  python classify.py [--force]

"""
from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

import config


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if not s:
        s = uuid.uuid4().hex[:8]
    return s[:150]


def read_raw_records(raw_dir: Path):
    for p in sorted(raw_dir.glob("*.json")):
        try:
            with p.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            print(f"Skipping {p.name}: can't read/parse JSON: {exc}", file=sys.stderr)
            continue
        data.setdefault("_raw_path", str(p))
        data.setdefault("id", p.stem)
        yield data


def wiki_has_raw(raw_id: str, wiki_dir: Path) -> bool:
    # Fast scan for front-matter raw_id in existing wiki files
    pattern = f"raw_id: {raw_id}"
    for md in wiki_dir.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        if pattern in text:
            return True
    return False


def choose_para(content: str) -> str:
    c = content.lower()
    if any(k in c for k in ("project", "milestone", "deliverable", "todo", "task", "epic")):
        return "Projects"
    if any(k in c for k in ("area", "role", "responsibility", "focus")):
        return "Areas"
    if any(k in c for k in ("http", "https", "link", "reference", "guide", "how to", "how-to", "readme", "doc")):
        return "Resources"
    if any(k in c for k in ("archive", "archived", "old note")):
        return "Archives"
    # fallback: short notes -> Resources, long notes -> Projects
    if len(content) > 400:
        return "Projects"
    return "Resources"


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "are",
    "not",
    "but",
    "you",
    "your",
}


def extract_tags(content: str, max_tags: int = 5):
    tags = []
    # explicit #tags
    tags += re.findall(r"#(\w[\w-]+)", content)
    if tags:
        # normalize
        seen = []
        for t in tags:
            t = t.lower()
            if t not in seen:
                seen.append(t)
        return seen[:max_tags]
    # fallback: pick frequent words
    words = re.findall(r"[a-zA-Z]{4,}", content.lower())
    freqs = {}
    for w in words:
        if w in STOPWORDS:
            continue
        freqs[w] = freqs.get(w, 0) + 1
    most = sorted(freqs.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in most[:max_tags]]


def make_summary(content: str, max_len: int = 200) -> str:
    if not content:
        return ""
    s = content.strip().replace("\n", " ")
    # Take first sentence if possible
    m = re.search(r"(.*?[\.\!\?])(\s|$)", s)
    if m:
        sent = m.group(1).strip()
        if len(sent) <= max_len:
            return sent
    return s[:max_len].rstrip() + ("..." if len(s) > max_len else "")


def make_title(record: dict) -> str:
    # Prefer explicit title, then first heading/line
    for key in ("title", "name", "headline"):
        if key in record and record[key]:
            return str(record[key]).strip()
    content = (record.get("content") or record.get("text") or "").strip()
    if not content:
        return f"Note {record.get('id')[:8]}"
    # If content starts with markdown heading
    m = re.match(r"^#\s*(.+)$", content.splitlines()[0])
    if m:
        return m.group(1).strip()
    # else first non-empty line
    for line in content.splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return f"Note {record.get('id')[:8]}"


def write_wiki(note: dict, para: str, wiki_dir: Path):
    title = note["title"]
    slug = slugify(title)
    folder = wiki_dir / para
    folder.mkdir(parents=True, exist_ok=True)
    candidate = folder / f"{slug}.md"
    suffix = 0
    while candidate.exists():
        suffix += 1
        candidate = folder / f"{slug}-{suffix}.md"
    fm = {
        "id": note["id"],
        "raw_id": note.get("raw_id") or note.get("id"),
        "para": para,
        "tags": note.get("tags", []),
        "summary": note.get("summary", ""),
        "title": title,
        "created_at": note.get("created_at") or now_iso(),
        "classified_at": now_iso(),
    }
    # Build YAML front matter manually (avoid external deps)
    fm_lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            fm_lines.append(f"{k}:")
            for item in v:
                fm_lines.append(f"  - '{str(item).replace("'", "\'\'")}'")
        else:
            val = str(v).replace("'", "''")
            fm_lines.append(f"{k}: '{val}'")
    fm_lines.append("---\n")

    body = note.get("body") or note.get("content") or ""
    text = "\n".join(fm_lines) + body + "\n"
    candidate.write_text(text, encoding="utf-8")
    return candidate


def classify_record(record: dict) -> dict:
    content = (record.get("content") or record.get("text") or "")
    title = make_title(record)
    para = choose_para(content)
    tags = extract_tags(content)
    summary = make_summary(content)
    note = {
        "id": uuid.uuid4().hex,
        "raw_id": record.get("id") or record.get("raw_id"),
        "title": title,
        "body": content,
        "content": content,
        "tags": tags,
        "summary": summary,
        "created_at": record.get("captured_at") or now_iso(),
    }
    return note


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Classify raw captures into PARA wiki notes (Phase 2.1)")
    p.add_argument("--force", action="store_true", help="Re-classify even if wiki entry already exists")
    args = p.parse_args(argv)

    config.ensure_project_dirs()

    if config.groq_configured():
        print("GROQ_API_KEY present: remote classification could be used (not implemented). Using local heuristic classifier.")
    else:
        print("GROQ_API_KEY not set — using local heuristic classifier.")

    raw_iter = list(read_raw_records(config.RAW_DIR))
    if not raw_iter:
        print(f"No raw JSON captures found in {config.RAW_DIR}")
        return

    created = 0
    skipped = 0
    for rec in raw_iter:
        raw_id = rec.get("id") or Path(rec.get("_raw_path", "")).stem
        if not args.force and wiki_has_raw(raw_id, config.WIKI_DIR):
            print(f"Skipping {raw_id}: already classified")
            skipped += 1
            continue
        try:
            note = classify_record(rec)
            path = write_wiki(note, note.get("para") or choose_para(note.get("content","")), config.WIKI_DIR)
            print(f"Created: {path} (raw: {raw_id})")
            created += 1
        except Exception as exc:
            print(f"Failed to classify {raw_id}: {exc}", file=sys.stderr)

    print(f"Summary: created={created} skipped={skipped} total={len(raw_iter)}")


if __name__ == "__main__":
    main()
