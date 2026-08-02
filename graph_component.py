#!/usr/bin/env python3
"""
graph_component.py — Python helpers for the Sub-Phase 4.2 knowledge graph.

Implements the "inline HTML builder in Python" half of the plan
(see docs/implementation-plan.md §4.2).  The HTML/JS side lives in
`static/graph_component.html` (vis-network, MIT, pinned + SRI).

This module is intentionally minimal: it only knows how to

  1. Resolve the canonical graph.json path (architecture §4.3).
  2. Load graph.json safely and tolerate the empty / missing cases
     flagged by edge-cases GRF-01 and UI-01.
  3. Read static/graph_component.html as a Jinja-free template and
     inject the JSON as a `__INLINE_GRAPH_DATA__` global so the same
     file works inside Streamlit's sandboxed iframe (which cannot
     fetch from the file-system) and as a plain standalone page.
  4. Provide a `render_in_streamlit(height=...)` entry point used by
     the minimal Phase 4 preview stub `graph_preview.py` and
     re-used in Phase 5 by `app.py`.

Out of scope here (lives in other phases):
  - Capture / classify / link / build_graph orchestration.
  - Ask / RAG.
  - Subprocess / pipeline buttons.

Usage (from a Streamlit script):
    from graph_component import render_in_streamlit
    render_in_streamlit(height=680)

Usage (programmatic):
    from graph_component import load_graph_data, build_inlined_html
    data = load_graph_data()
    html = build_inlined_html(data)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import config
from lib import storage

# ── Constants ─────────────────────────────────────────────────────────────
HTML_TEMPLATE_PATH: Path = config.PROJECT_ROOT / "static" / "graph_component.html"
DEFAULT_HEIGHT: int = 680

# Marker token inside the template where graph JSON is injected.  Keeping
# it as an explicit comment (rather than a generic `</head>` replacement)
# means the rest of the HTML is opaque to graph_component.py.
_INLINE_MARKER = "<!-- __INLINE_GRAPH_DATA__ -->"


# ── Data loading ─────────────────────────────────────────────────────────
def load_graph_data(graph_path: Path | None = None) -> dict[str, Any]:
    """
    Load `graph.json` and return its parsed dict.

    Returns an empty graph (not a Python error) when the file is missing
    or invalid, so the UI can render its "no graph yet" empty state
    (edge-cases GRF-01, UI-01).
    """
    path = Path(graph_path) if graph_path is not None else config.GRAPH_PATH
    empty: dict[str, Any] = {"meta": {"note_count": 0, "edge_count": 0}, "nodes": [], "edges": []}

    if not path.exists():
        return empty
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return empty
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return empty

    # Tolerate both the architecture §4.3 `meta` block and the legacy
    # `metadata` block used by older builds.
    if "meta" not in data and "metadata" in data:
        data["meta"] = data["metadata"]
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    data["meta"].setdefault("note_count", len(data["nodes"]))
    data["meta"].setdefault("edge_count", len(data["edges"]))
    return data


# ── HTML template handling ────────────────────────────────────────────────
def _read_template(path: Path | None = None) -> str:
    """Read the HTML template, raising a clear error if it is missing."""
    p = Path(path) if path is not None else HTML_TEMPLATE_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Graph HTML template not found at '{p}'.  "
            "Ensure static/graph_component.html exists (Sub-Phase 4.2)."
        )
    return p.read_text(encoding="utf-8")


def build_inlined_html(
    graph_data: dict[str, Any] | None = None,
    *,
    template_path: Path | None = None,
) -> str:
    """
    Return the HTML string with graph data injected inline.

    The injection sets a global `__INLINE_GRAPH_DATA__` that the
    page script prefers over its `fetch()` fallback.  Falls back to
    a no-data injection if `graph_data` is None.
    """
    html = _read_template(template_path)
    payload = json.dumps(graph_data or {}, ensure_ascii=False)
    # Use a JSON-safe assignment (no HTML-significant characters can
    # come out of json.dumps, but escape the closing </script> just
    # in case future data sources include raw script tags).
    safe_payload = payload.replace("</", "<\\/")
    inject = (
        f"<script>\n"
        f"// Injected by graph_component.py — Sub-Phase 4.2 inline data.\n"
        f"window.__INLINE_GRAPH_DATA__ = {safe_payload};\n"
        f"</script>\n"
    )
    if _INLINE_MARKER in html:
        return html.replace(_INLINE_MARKER, inject, 1)
    # Backwards-compat: legacy templates used `</head>` as the anchor.
    return html.replace("</head>", inject + "</head>", 1)


# ── Streamlit integration ────────────────────────────────────────────────
def render_in_streamlit(
    graph_path: Path | None = None,
    *,
    height: int = DEFAULT_HEIGHT,
) -> None:
    """
    Render the graph inside a running Streamlit app.

    Reads `graph.json` (or `graph_path`), injects it into the HTML
    template, and embeds the result via `st.components.v1.html`.
    Falls back to a friendly in-app message if `graph.json` is
    missing so the page does not crash (edge-case UI-01).
    """
    import streamlit as st
    import streamlit.components.v1 as components

    data = load_graph_data(graph_path)
    note_count = (data.get("meta") or {}).get("note_count", 0)
    edge_count = (data.get("meta") or {}).get("edge_count", 0)

    # Stale-state notice (edge-case PL-02): the file is present but
    # the wiki may have changed since the last build.
    if not data["nodes"]:
        st.info(
            "**`graph.json` is missing or empty.**  "
            "Run `python build_graph.py` to (re)generate the graph from "
            "`wiki/`, then refresh this page."
        )
        st.stop()

    if note_count == 0:
        st.info(
            "The wiki is currently empty. Capture a note with "
            "`python capture.py note \"...\"`, run `python classify.py`, "
            "`python link.py`, and finally `python build_graph.py`."
        )
        st.stop()

    components.html(build_inlined_html(data), height=height, scrolling=False)


# ── CLI smoke test ────────────────────────────────────────────────────────
def _print_summary(data: dict[str, Any]) -> None:
    meta = data.get("meta") or {}
    print(
        f"graph.json — nodes={meta.get('note_count', len(data.get('nodes', [])))}, "
        f"edges={meta.get('edge_count', len(data.get('edges', [])))}"
    )


def main() -> int:
    """CLI entry point: load graph.json, report counts, write inlined HTML to stdout for smoke testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Sub-Phase 4.2 graph component helpers.")
    parser.add_argument(
        "--graph", type=Path, default=None,
        help="Path to graph.json (default: config.GRAPH_PATH).",
    )
    parser.add_argument(
        "--print-html", action="store_true",
        help="Print the inlined HTML to stdout (very large; for smoke tests only).",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print a one-line summary of node/edge counts and exit.",
    )
    args = parser.parse_args()

    data = load_graph_data(args.graph)
    if args.stats:
        _print_summary(data)
        return 0
    if args.print_html:
        print(build_inlined_html(data))
        return 0
    _print_summary(data)
    print(f"Template: {HTML_TEMPLATE_PATH} ({'present' if HTML_TEMPLATE_PATH.exists() else 'MISSING'})")
    print("Use `streamlit run graph_preview.py` to render the graph in a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
