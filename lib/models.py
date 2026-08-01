"""
lib/models.py — shared dataclasses for SecondSelf.

All models are plain dataclasses (no external deps) so every phase can import
them without pulling in heavy libraries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ── Phase 0 / Phase 1 ─────────────────────────────────────────────────────────

@dataclass
class CaptureMeta:
    """Metadata written to raw/{id}/meta.json."""
    id: str                       # {YYYY-MM-DD}_{uuid8}
    timestamp: str                # ISO-8601 UTC
    type: str                     # "note" | "link" | "file"
    source: str                   # original text / URL / filename
    original_filename: Optional[str] = None
    content_hash: Optional[str] = None   # SHA-256 hex for dedup detection


@dataclass
class CaptureResult:
    """Returned by every capture_*() function."""
    id: str
    path: str     # relative path to raw/{id}/ folder
    type: str     # "note" | "link" | "file"


# ── Phase 2 ───────────────────────────────────────────────────────────────────

@dataclass
class WikiNote:
    """Represents a parsed wiki/{para}/{id}.md file."""
    id: str
    raw_id: str
    para: str                          # Projects | Areas | Resources | Archives
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    created: str = ""                  # ISO-8601
    links: List[str] = field(default_factory=list)   # linked note IDs
    body: str = ""                     # Markdown body (no front matter)


# ── Phase 3 ───────────────────────────────────────────────────────────────────

@dataclass
class GraphNode:
    """A node in the exported knowledge graph."""
    id: str
    label: str          # shown on graph — derived from summary or title
    para: str           # PARA category → determines colour group
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    content_preview: str = ""   # first ~200 chars of body
    group: str = ""             # same as para; kept separate for vis-network grouping


@dataclass
class GraphEdge:
    """A directed edge in the knowledge graph."""
    source: str
    target: str
    weight: float = 1.0
    type: str = "wikilink"     # "wikilink" | "similarity"


# ── Phase 4 ───────────────────────────────────────────────────────────────────

@dataclass
class AskResult:
    """Returned by ask.ask()."""
    answer: str
    sources: List[dict] = field(default_factory=list)
    # Each source: {"id": str, "summary": str, "relevance_score": float, "para": str}
