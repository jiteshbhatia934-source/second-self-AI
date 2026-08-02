#!/usr/bin/env python3
"""
build_graph.py — derive graph structure from wiki notes and export graph.json

Implements Phase 4 / Sub-Phase 4.1 from docs/implementation-plan.md.

Schema (architecture §4.3):
  {
    "meta":  {"generated_at": ISO-8601, "note_count": N, "edge_count": M},
    "nodes": [{"id","label","para","tags","summary","path", + "content_preview","group"}],
    "edges": [{"source","target","type": "wikilink" | "similarity", "weight"}]
  }

Behavior (plan §4.1):
  1. Walk wiki/**/*.md via lib/storage.read_wiki_notes()
  2. Parse front matter + body wikilinks [[...]]
  3. Resolve link targets to a node id (by id, slug, title, or filename)
  4. Build nodes: id, label (title -> summary -> slug), para, tags, summary,
     path (wiki/<relative>), content_preview (optional snippet), group (= para)
  5. Build edges: `wikilink` (explicit links) and `similarity` when a note tracks
     similarity links separately in front matter (`similar` / `similar_notes`)
  6. Write graph.json with a `meta` block to config.GRAPH_PATH (atomic write)
  7. Log unresolved links to stderr; include orphan nodes (0 edges)

Usage:
  python build_graph.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
from lib import storage
from lib.models import GraphEdge, GraphNode

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

# Front-matter keys that (optionally) hold similarity links tracked separately
# from explicit body wikilinks. When present they are emitted as `similarity`
# edges so the UI can style them differently (architecture §4.3).
_SIMILARITY_KEYS = ("similar", "similar_notes", "similarity_links")


def _snippet(body: str, max_chars: int = 200) -> str:
    """Extract a clean plain-text preview from a markdown body."""
    text = re.sub(r"```.*?```", "", body, flags=re.S)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"[*_]{1,2}", "", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars].rstrip()


def _normalize(value: str) -> str:
    """Slug-like normalisation used as a last-resort resolution key."""
    return re.sub(r"[^a-z0-9-]", "-", value.lower()).strip("-")


def _node_path(note) -> str:
    """Return the project-relative wiki path, e.g. 'wiki/Resources/foo.md'."""
    rel = str(getattr(note, "path", "") or "").replace("\\", "/")
    if not rel:
        slug = getattr(note, "slug", "") or note.id
        rel = f"{note.para}/{slug}.md"
    return f"{config.WIKI_DIR.name}/{rel}"


def build_graph(
    wiki_dir: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    """Build the knowledge graph, write it to `output_path`, and return the dict."""
    config.ensure_project_dirs()
    wiki_dir = wiki_dir or config.WIKI_DIR
    output_path = output_path or config.GRAPH_PATH

    notes = (
        storage.read_wiki_notes()
        if wiki_dir == config.WIKI_DIR
        else _read_notes_from(wiki_dir)
    )

    # ── Build nodes + resolution lookup ──────────────────────────────────────
    # Maps any resolvable string (id, slug, title, filename) → node id.
    target_lookup: dict[str, str] = {}
    raw_nodes: list[GraphNode] = []

    for note in notes:
        node_id = note.id
        label = note.title or note.summary or getattr(note, "slug", "") or node_id

        raw_nodes.append(GraphNode(
            id=node_id,
            label=label,
            para=note.para,
            title=note.title,
            path=_node_path(note),
            tags=note.tags,
            summary=note.summary,
            content_preview=_snippet(note.body),
            group=note.para,
        ))

        # Register every string that could appear inside a [[wikilink]].
        candidates = {node_id, label, note.title, getattr(note, "slug", "")}
        for cand in candidates:
            if not cand:
                continue
            target_lookup.setdefault(cand, node_id)
            target_lookup.setdefault(cand.lower(), node_id)
            target_lookup.setdefault(_normalize(cand), node_id)

    valid_ids: set[str] = {n.id for n in raw_nodes}

    def _resolve(raw_target: str) -> str | None:
        t = raw_target.strip()
        if not t:
            return None
        return (
            target_lookup.get(t)
            or target_lookup.get(t.lower())
            or target_lookup.get(_normalize(t))
        )

    # ── Build edges ──────────────────────────────────────────────────────────
    seen_edge_keys: set[tuple] = set()
    edges: list[GraphEdge] = []

    def _add_edge(src: str, raw_target: str, edge_type: str) -> None:
        resolved = _resolve(raw_target)
        if not resolved or resolved not in valid_ids:
            print(
                f"[WARNING] Unresolved {edge_type} link '[[{raw_target.strip()}]]' "
                f"in note '{src}'",
                file=sys.stderr,
            )
            return
        if resolved == src:
            return  # skip self-links
        # Undirected dedup key, distinct per edge type.
        key = (min(src, resolved), max(src, resolved), edge_type)
        if key in seen_edge_keys:
            return
        seen_edge_keys.add(key)
        edges.append(GraphEdge(source=src, target=resolved, weight=1.0, type=edge_type))

    for note in notes:
        src = note.id

        # Explicit links: front-matter links[] + [[wikilinks]] in the body.
        for raw_target in list(note.links) + WIKILINK_RE.findall(note.body):
            _add_edge(src, raw_target, "wikilink")

        # Optional similarity links tracked separately in front matter.
        for target in _similarity_targets(note):
            _add_edge(src, target, "similarity")

    # ── Serialise (architecture §4.3) ────────────────────────────────────────
    nodes_export = [
        {
            "id": n.id,
            "label": n.label,
            "para": n.para,
            "tags": n.tags,
            "summary": n.summary,
            "path": n.path,
            "content_preview": n.content_preview,
            "group": n.group,
        }
        for n in raw_nodes
    ]
    edges_export = [
        {"source": e.source, "target": e.target, "type": e.type, "weight": e.weight}
        for e in edges
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    graph_data = {
        "meta": {
            "generated_at": now_iso,
            "note_count": len(nodes_export),
            "edge_count": len(edges_export),
        },
        "nodes": nodes_export,
        "edges": edges_export,
    }

    # Atomic write.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(output_path)

    # Record the build time in the index (best effort).
    try:
        idx = storage.load_index()
        idx["last_graph_build"] = now_iso
        storage.save_index(idx)
    except Exception:
        pass

    print(
        f"Exported graph -> {output_path} "
        f"({len(nodes_export)} nodes, {len(edges_export)} edges)"
    )
    return graph_data


def _similarity_targets(note) -> list[str]:
    """Return similarity link targets if the note tracks them separately."""
    targets: list[str] = []
    for key in _SIMILARITY_KEYS:
        value = getattr(note, key, None)
        if isinstance(value, str):
            targets.append(value)
        elif isinstance(value, (list, tuple)):
            targets.extend(str(v) for v in value)
    return targets


def _read_notes_from(wiki_dir: Path):
    """Fallback reader for an arbitrary wiki dir (used in tests)."""
    from lib.models import WikiNote
    from lib.storage import parse_front_matter

    notes = []
    for path in sorted(wiki_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_front_matter(text)
            body_links = WIKILINK_RE.findall(body)
            links = list(meta.get("links") or []) + body_links
            links = list(dict.fromkeys(links))
            notes.append(WikiNote(
                id=str(meta.get("id") or path.stem),
                raw_id=str(meta.get("raw_id") or ""),
                slug=path.stem,
                title=str(meta.get("title") or ""),
                path=str(path.relative_to(wiki_dir)),
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


def main() -> None:
    build_graph()


if __name__ == "__main__":
    main()
