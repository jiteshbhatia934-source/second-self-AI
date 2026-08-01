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

# ── Ask and Capture UI ───────────────────────────────────────────────────────
with st.expander("Ask your wiki (Question)", expanded=True):
    question = st.text_input("Ask a question", key="ask_question")
    ask_btn = st.button("Ask", key="ask_button")
    if ask_btn:
        if not question.strip():
            st.warning("Please enter a non-empty question.")
        else:
            with st.spinner("Searching notes…"):
                try:
                    # Import the local ask module and call ask() directly so we avoid shelling out.
                    import ask as ask_mod
                    result = ask_mod.ask(question)
                    st.markdown("**Answer:**")
                    st.write(result.get("answer"))
                    if result.get("sources"):
                        st.markdown("**Sources:**")
                        for src in result.get("sources", []):
                            st.write(f"- {src.get('title')} ({src.get('path')}) — score={src.get('relevance_score'):.3f}")
                except Exception as exc:  # pragma: no cover - runtime UI handling
                    st.error(f"Ask failed: {exc}")

with st.expander("Capture note / link / file", expanded=False):
    cap_type = st.radio("Capture type", ["note", "link", "file"], horizontal=True, key="capture_type")
    if cap_type == "note":
        note_text = st.text_area("Note text", height=120, key="note_text")
        if st.button("Capture note", key="capture_note_btn"):
            if not note_text.strip():
                st.warning("Enter note text to capture.")
            else:
                try:
                    import capture as cap_mod
                    cap_mod.capture_note(note_text)
                    st.success("Captured note into raw/ — run classify.py to import into wiki/")
                except Exception as exc:  # pragma: no cover - runtime UI handling
                    st.error(f"Capture note failed: {exc}")
    elif cap_type == "link":
        url = st.text_input("URL to capture (include https://)", key="capture_link_url")
        if st.button("Capture link", key="capture_link_btn"):
            if not url.strip():
                st.warning("Enter a URL to capture.")
            else:
                try:
                    import capture as cap_mod
                    cap_mod.capture_link(url.strip())
                    st.success("Captured link into raw/ — run classify.py to import into wiki/")
                except Exception as exc:  # pragma: no cover - runtime UI handling
                    st.error(f"Capture link failed: {exc}")
    else:
        uploaded = st.file_uploader("Upload file to capture", key="capture_file_uploader")
        if uploaded is not None:
            st.write(f"Selected file: {uploaded.name} ({uploaded.type})")
            if st.button("Upload and capture file", key="capture_file_btn"):
                try:
                    import tempfile
                    tmpdir = Path(config.PROJECT_ROOT) / "tmp_uploads"
                    tmpdir.mkdir(parents=True, exist_ok=True)
                    save_to = tmpdir / uploaded.name
                    # Write the uploaded file to disk so capture_file() can copy it into raw/files
                    with open(save_to, "wb") as fh:
                        fh.write(uploaded.getbuffer())
                    import capture as cap_mod
                    cap_mod.capture_file(save_to)
                    st.success(f"Captured file: {uploaded.name} into raw/files — run classify.py to import into wiki/")
                except Exception as exc:  # pragma: no cover - runtime UI handling
                    st.error(f"Capture file failed: {exc}")


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
