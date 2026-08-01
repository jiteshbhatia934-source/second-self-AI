#!/usr/bin/env python3
"""
graph_preview.py — Streamlit preview stub for the SecondSelf knowledge graph.

This is the thin Phase 3 preview app; it will be merged into app.py in Phase 4.

Usage:
  streamlit run graph_preview.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import config
import build_graph

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecondSelf — Knowledge Graph",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #07101f; }
  [data-testid="stHeader"]           { background: transparent; }
  header { visibility: hidden; }
  .stButton > button {
    background: linear-gradient(135deg, #0369a1, #4338ca);
    color: #fff; border: none; font-weight: 500; border-radius: 8px;
  }
  .stButton > button:hover { opacity: 0.88; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_btn = st.columns([6, 1])
with col_title:
    st.markdown("## ⬡ SecondSelf — Knowledge Graph")
with col_btn:
    rebuild = st.button("🔄 Rebuild", help="Re-run build_graph.py and refresh")

# ── Rebuild on demand ─────────────────────────────────────────────────────────
if rebuild:
    with st.spinner("Rebuilding graph from wiki notes…"):
        try:
            data = build_graph.build_graph()
            st.success(
                f"Rebuilt — {data['metadata']['node_count']} nodes, "
                f"{data['metadata']['edge_count']} edges."
            )
        except Exception as exc:
            st.error(f"Build failed: {exc}")

# ── Canonical paths (new plan) ────────────────────────────────────────────────
GRAPH_JSON   = config.DATA_DIR / "graph.json"        # data/graph.json
GRAPH_HTML   = config.PROJECT_ROOT / "static" / "graph.html"   # static/graph.html

# ── Guard: graph.json must exist ─────────────────────────────────────────────
if not GRAPH_JSON.exists():
    st.warning(
        "**`data/graph.json` not found.**  "
        "Click **Rebuild** above or run `python build_graph.py` in your terminal."
    )
    st.stop()

try:
    graph_data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
except Exception as exc:
    st.error(f"Failed to parse `data/graph.json`: {exc}")
    st.stop()

# ── Stats row — use "metadata" key (new schema) ───────────────────────────────
meta = graph_data.get("metadata", {})
c1, c2, c3 = st.columns(3)
c1.metric("📄 Notes", meta.get("node_count", len(graph_data.get("nodes", []))))
c2.metric("🔗 Links", meta.get("edge_count",  len(graph_data.get("edges", []))))
if meta.get("generated_at"):
    try:
        ts = datetime.fromisoformat(meta["generated_at"])
        ts_str = ts.astimezone(tz=None).strftime("%d %b %Y, %H:%M")
    except Exception:
        ts_str = meta["generated_at"]
    c3.metric("🕒 Built", ts_str)

st.divider()

# ── Render static/graph.html with inlined data ────────────────────────────────
if not GRAPH_HTML.exists():
    st.error(
        f"`static/graph.html` not found at `{GRAPH_HTML}`.  "
        "Ensure the Sub-Phase 3.2 file exists."
    )
    st.stop()

html_src = GRAPH_HTML.read_text(encoding="utf-8")

# Inline graph data so it works inside Streamlit's sandboxed iframe
# (no cross-origin fetch to the filesystem is possible in iframes).
json_inline = json.dumps(graph_data, ensure_ascii=False)

inject = (
    "<script>\n"
    "// Injected by graph_preview.py — graph data inlined for Streamlit sandbox\n"
    f"var __INLINE_GRAPH_DATA__ = {json_inline};\n"
    "</script>\n"
)
html_src = html_src.replace("</head>", inject + "</head>", 1)

# static/graph.html already checks for __INLINE_GRAPH_DATA__ before fetch().
components.html(html_src, height=680, scrolling=False)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;font-size:0.72rem;color:#475569;margin-top:4px'>"
    "SecondSelf · Phase 3 Graph Preview · vis-network MIT · "
    f"<code>{GRAPH_JSON.relative_to(config.PROJECT_ROOT)}</code>"
    "</div>",
    unsafe_allow_html=True,
)
