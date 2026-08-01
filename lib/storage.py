"""
lib/storage.py — filesystem helpers for SecondSelf.

Provides:
  generate_capture_id()   → {YYYY-MM-DD}_{uuid8}
  write_raw_capture()     → raw/{id}/meta.json + content file
  read_raw_captures()     → list unprocessed raw items
  write_wiki_note()       → wiki/{para}/{id}.md with YAML frontmatter
  read_wiki_notes()       → parse all wiki markdown files
  load_index()            → data/index.json
  save_index()            → data/index.json (atomic write)
  content_hash()          → SHA-256 hex
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.models import CaptureMeta, CaptureResult, WikiNote

# ── Lazy import of project root so storage doesn't depend on config at import ──
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _raw_dir() -> Path:
    try:
        import config
        return config.RAW_DIR
    except Exception:
        return _project_root() / "raw"


def _wiki_dir() -> Path:
    try:
        import config
        return config.WIKI_DIR
    except Exception:
        return _project_root() / "wiki"


def _data_dir() -> Path:
    try:
        import config
        return config.DATA_DIR
    except Exception:
        return _project_root() / "data"


# ── Regex helpers ─────────────────────────────────────────────────────────────
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


# ─────────────────────────────────────────────────────────────────────────────
# ID / Hashing
# ─────────────────────────────────────────────────────────────────────────────

def generate_capture_id() -> str:
    """Return a sortable unique ID: {YYYY-MM-DD}_{8-char uuid hex}."""
    date_part = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    uid_part = uuid.uuid4().hex[:8]
    return f"{date_part}_{uid_part}"


def content_hash(data: str | bytes) -> str:
    """Return SHA-256 hex digest — used for dedup/change detection."""
    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")
    return hashlib.sha256(data).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Raw captures
# ─────────────────────────────────────────────────────────────────────────────

def write_raw_capture(
    meta: CaptureMeta,
    content: str | bytes,
    ext: str = "md",
) -> CaptureResult:
    """
    Create raw/{id}/meta.json and raw/{id}/content.{ext}.
    Returns CaptureResult with the folder path.
    """
    raw_dir = _raw_dir()
    folder = raw_dir / meta.id
    folder.mkdir(parents=True, exist_ok=True)

    # Write meta.json
    meta_dict = {
        "id": meta.id,
        "timestamp": meta.timestamp,
        "type": meta.type,
        "source": meta.source,
        "original_filename": meta.original_filename,
        "content_hash": meta.content_hash,
    }
    (folder / "meta.json").write_text(
        json.dumps(meta_dict, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write content file
    content_path = folder / f"content.{ext}"
    if isinstance(content, bytes):
        content_path.write_bytes(content)
    else:
        content_path.write_text(content, encoding="utf-8")

    return CaptureResult(id=meta.id, path=str(folder.relative_to(raw_dir.parent)), type=meta.type)


def read_raw_captures(skip_processed: Optional[set] = None) -> List[Dict[str, Any]]:
    """
    Yield dicts from raw/{id}/meta.json.
    If skip_processed is given (set of IDs already in index.json), skip those.
    """
    raw_dir = _raw_dir()
    results = []
    for folder in sorted(raw_dir.iterdir()):
        if not folder.is_dir():
            continue
        meta_path = folder / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if skip_processed and meta.get("id") in skip_processed:
            continue
        # Attach content path
        content_files = list(folder.glob("content.*"))
        meta["_content_path"] = str(content_files[0]) if content_files else None
        meta["_folder"] = str(folder)
        results.append(meta)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Wiki notes
# ─────────────────────────────────────────────────────────────────────────────


def parse_front_matter(text: str) -> tuple[Dict[str, Any], str]:
    """Return (meta_dict, body_str) from a markdown file."""
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text

    fm_raw = m.group(1)
    body = m.group(2)
    meta: Dict[str, Any] = {}

    # Try PyYAML first
    try:
        import yaml  # type: ignore
        parsed = yaml.safe_load(fm_raw)
        if isinstance(parsed, dict):
            meta = parsed
    except Exception:
        pass

    if not meta:
        # Fallback line parser
        cur_key: Optional[str] = None
        for line in fm_raw.splitlines():
            if not line.strip():
                continue
            if (line.startswith(" ") or line.startswith("\t")) and cur_key:
                if line.strip().startswith("-"):
                    val = line.strip().lstrip("- ").strip().strip("'\"")
                    meta.setdefault(cur_key, []).append(val)
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                meta[k] = [] if v == "" else v.strip("'\"")
                cur_key = k

    # Normalise tags
    tags = meta.get("tags")
    if isinstance(tags, str):
        meta["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    elif isinstance(tags, list):
        meta["tags"] = [str(t).strip() for t in tags]
    else:
        meta["tags"] = []

    return meta, body


# Keep private alias for backward-compat with any internal callers
_parse_front_matter = parse_front_matter



def write_wiki_note(note: WikiNote) -> Path:
    """
    Write wiki/{para}/{id}.md with YAML front matter.
    Returns the path written.
    """
    wiki_dir = _wiki_dir()
    para_dir = wiki_dir / note.para
    para_dir.mkdir(parents=True, exist_ok=True)

    # Serialize tags and links as proper YAML lists ([] for empty, items for non-empty)
    def _yaml_list(items: list) -> str:
        if not items:
            return "[]"
        return "\n" + "\n".join(f"  - {item}" for item in items)

    safe_summary = note.summary.replace('"', "'")
    front_matter = (
        f"---\n"
        f"id: {note.id}\n"
        f"raw_id: {note.raw_id}\n"
        f"para: {note.para}\n"
        f"tags: {_yaml_list(note.tags)}\n"
        f'summary: "{safe_summary}"\n'
        f"created: {note.created}\n"
        f"links: {_yaml_list(note.links)}\n"
        f"---\n"
    )
    content = front_matter + "\n" + note.body.lstrip()

    target = para_dir / f"{note.id}.md"
    # Atomic write
    tmp = target.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)
    return target


def read_wiki_notes() -> List[WikiNote]:
    """Parse all wiki/**/*.md files and return WikiNote objects."""
    wiki_dir = _wiki_dir()
    notes: List[WikiNote] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_front_matter(text)
            # Collect wikilinks from body
            body_links = _WIKILINK_RE.findall(body)
            links = list(meta.get("links") or []) + body_links
            links = list(dict.fromkeys(links))  # deduplicate, preserve order

            notes.append(WikiNote(
                id=str(meta.get("id") or path.stem),
                raw_id=str(meta.get("raw_id") or ""),
                slug=path.stem,
                title=str(meta.get("title") or ""),
                path=str(path.relative_to(_wiki_dir())),
                para=str(meta.get("para") or path.parent.name),
                tags=meta.get("tags") or [],
                summary=str(meta.get("summary") or ""),
                created=str(meta.get("created") or ""),
                links=links,
                body=body,
            ))
        except Exception:
            continue
    return notes


# ─────────────────────────────────────────────────────────────────────────────
# Index (data/index.json)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_INDEX: Dict[str, Any] = {
    "raw_processed": {},          # {capture_id: {wiki_id, classified_at}}
    "embeddings_version": "all-MiniLM-L6-v2",
    "last_graph_build": None,
}


def _index_path() -> Path:
    return _data_dir() / "index.json"


def load_index() -> Dict[str, Any]:
    """Load data/index.json; return default structure if missing or corrupt."""
    p = _index_path()
    if not p.exists():
        return dict(_DEFAULT_INDEX)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # Ensure required keys exist
        for k, v in _DEFAULT_INDEX.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(_DEFAULT_INDEX)


def save_index(index: Dict[str, Any]) -> None:
    """Atomically write data/index.json."""
    p = _index_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
