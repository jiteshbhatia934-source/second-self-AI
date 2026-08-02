#!/usr/bin/env python3
"""
graph_preview.py — Sub-Phase 4.2 minimal Streamlit preview stub.

Per docs/implementation-plan.md §4.2:
  "Standalone test: open HTML with local `graph.json` OR
   minimal `streamlit run` stub that only shows graph."

This script is intentionally thin. It only:
  1. Sets a dark-mode page chrome to match the embedded graph.
  2. Renders a small header with the current wiki/edge counts.
  3. Delegates rendering to `graph_component.render_in_streamlit`.

Capture / classify / link / build_graph orchestration lives in
`pipeline.py`; ask / RAG lives in `ask.py` and Phase 5's `app.py`.
They are deliberately not exposed here so this stub stays focused on
Sub-Phase 4.2 acceptance criteria:

  - [ ] Interactive force-directed graph renders from that JSON
  - [ ] Hover reveals note content
  - [ ] Drag + zoom work
  - [ ] Built from your real notes, not dummy data

Usage:
  streamlit run graph_preview.py
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

import config
from graph_component import render_in_streamlit

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecondSelf — Knowledge Graph",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Subtle dark theme so the embedded graph blends in.
st.markdown(
    """
    <style>
      [data-testid="stAppViewContainer"] { background: #07101f; }
      [data-testid="stHeader"]            { background: transparent; }
      header                              { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────────────────
st.markdown("## ⬡ SecondSelf — Knowledge Graph")

# ── Stats row (architecture §4.3 meta block) ─────────────────────────────
GRAPH_JSON = config.GRAPH_PATH
graph_data: dict = {}
if GRAPH_JSON.exists():
    try:
        graph_data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        graph_data = {}

meta = graph_data.get("meta") or graph_data.get("metadata") or {}
note_count = meta.get("note_count", meta.get("node_count", len(graph_data.get("nodes", []))))
edge_count = meta.get("edge_count", len(graph_data.get("edges", [])))

c1, c2, c3 = st.columns(3)
c1.metric("📄 Notes", note_count)
c2.metric("🔗 Links", edge_count)
if meta.get("generated_at"):
    try:
        ts = datetime.fromisoformat(meta["generated_at"])
        ts_str = ts.astimezone().strftime("%d %b %Y, %H:%M")
    except ValueError:
        ts_str = meta["generated_at"]
    c3.metric("🕒 Built", ts_str)

st.divider()

# ── Render the graph (delegates to graph_component.py) ───────────────────
render_in_streamlit()

# ── Footer ───────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;font-size:0.72rem;color:#475569;margin-top:4px'>"
    "SecondSelf · Sub-Phase 4.2 · vis-network 9.1.9 (MIT) · "
    f"<code>{Path(GRAPH_JSON).name}</code>"
    "</div>",
    unsafe_allow_html=True,
)
