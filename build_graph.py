#!/usr/bin/env python3
"""
build_graph.py — derive graph structure from wiki notes and export data/graph.json

Implements Phase 3 / Sub-Phase 3.1 from implementation-plan.md

New schema (aligned with plan §3.1.2):
  {
    "nodes": [{"id","label","para","tags","summary","content_preview","group"}],
    "edges": [{"source","target","weight","type"}],
    "metadata": {"generated_at","node_count","edge_count"}
  }

Behavior:
  - Walks wiki/**/*.md via lib/storage.read_wiki_notes()
  - Builds nodes: id, label (summary or title or slug), para, tags, summary,
                  content_preview (first 200 chars), group (= para)
  - Parses edges from links[] frontmatter + [[wikilink]] in body
  - Deduplicates edges: key = (min(source,target), max(source,target), type)
  - Includes orphan nodes (0 edges)
  - Logs unresolved wikilinks to stderr
  - Writes data/graph.json atomically
  - Updates data/index.json["last_graph_build"]

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


def _snippet(body: str, max_chars: int = 200) -> str:
    """Extract a clean plain-text preview from markdown body."""
    text = re.sub(r"```.*?```", "", body, flags=re.S)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"[*_]{1,2}", "", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars].rstrip()


def build_graph(
    wiki_dir: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    """
    Build and return the graph dict; write to output_path atomically.
    """
    config.ensure_project_dirs()
    wiki_dir = wiki_dir or config.WIKI_DIR
    # New plan: output goes to data/graph.json
    output_path = output_path or (config.DATA_DIR / "graph.json")

    notes = storage.read_wiki_notes() if wiki_dir == config.WIKI_DIR else _read_notes_from(wiki_dir)

    # ── Build node lookup ─────────────────────────────────────────────────────
    # Maps any resolvable string (id, slug, title, filename) → node_id
    target_lookup: dict[str, str] = {}
    raw_nodes: list[GraphNode] = []

    for note in notes:
        node_id = note.id
        label = note.summary or note.id
        content_preview = _snippet(note.body)

        node = GraphNode(
            id=node_id,
            label=label,
            para=note.para,
            tags=note.tags,
            summary=note.summary,
            content_preview=content_preview,
            group=note.para,
        )
        raw_nodes.append(node)

        # Register lookup targets
        for key in {node_id, node_id.lower(), label, label.lower()}:
            target_lookup.setdefault(key, node_id)
        # Also register the filename stem (may differ from id)
        stem = re.sub(r"[^a-z0-9-]", "-", node_id.lower()).strip("-")
        target_lookup.setdefault(stem, node_id)

    # Precompute a set of valid node IDs for validation
    valid_ids: set[str] = {n.id for n in raw_nodes}

    # ── Build edges ───────────────────────────────────────────────────────────
    seen_edge_keys: set[tuple] = set()
    edges: list[GraphEdge] = []

    for note in notes:
        src = note.id

        # Collect all link targets from frontmatter links[] + body [[wikilinks]]
        body_links = WIKILINK_RE.findall(note.body)
        all_targets: list[str] = list(note.links) + body_links

        for raw_target in all_targets:
            t = raw_target.strip()
            if not t:
                continue

            # Resolve
            resolved = (
                target_lookup.get(t)
                or target_lookup.get(t.lower())
                or target_lookup.get(re.sub(r"[^a-z0-9-]", "-", t.lower()).strip("-"))
            )

            if not resolved or resolved not in valid_ids:
                print(f"[WARNING] Unresolved link '[[{t}]]' in note '{src}'", file=sys.stderr)
                continue

            if resolved == src:
                continue  # skip self-links

            # Deduplicate (undirected key per plan §3.1.1)
            edge_key = (min(src, resolved), max(src, resolved), "wikilink")
            if edge_key in seen_edge_keys:
                continue
            seen_edge_keys.add(edge_key)
            edges.append(GraphEdge(source=src, target=resolved, weight=1.0, type="wikilink"))

    # ── Serialise ─────────────────────────────────────────────────────────────
    nodes_export = [
        {
            "id": n.id,
            "label": n.label,
            "para": n.para,
            "tags": n.tags,
            "summary": n.summary,
            "content_preview": n.content_preview,
            "group": n.group,
        }
        for n in raw_nodes
    ]
    edges_export = [
        {"source": e.source, "target": e.target, "weight": e.weight, "type": e.type}
        for e in edges
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    graph_data = {
        "nodes": nodes_export,
        "edges": edges_export,
        "metadata": {
            "generated_at": now_iso,
            "node_count": len(nodes_export),
            "edge_count": len(edges_export),
        },
    }

    # Atomic write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(output_path)

    # Update index
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


def _read_notes_from(wiki_dir: Path):
    """Fallback: read notes from an arbitrary wiki dir (used in tests)."""
    import re as _re
    from lib.storage import parse_front_matter
    from lib.models import WikiNote

    _wl = _re.compile(r"\[\[([^\]]+)\]\]")
    notes = []
    for path in sorted(wiki_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_front_matter(text)
            body_links = _wl.findall(body)
            links = list(meta.get("links") or []) + body_links
            links = list(dict.fromkeys(links))
            notes.append(WikiNote(
                id=str(meta.get("id") or path.stem),
                raw_id=str(meta.get("raw_id") or ""),
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
