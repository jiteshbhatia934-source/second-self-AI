#!/usr/bin/env python3
"""
app.py — SecondSelf Streamlit shell (Phase 5 surface, Sub-Phase 4.2 graph core).

Brings the whole product into a single web UI:

  Sidebar
    • Capture      — quick note textarea → raw/ envelope
    • Pipeline     — Force re-process + Process new captures (classify → link → graph)
    • Stats        — wiki notes, graph nodes, graph edges

  Main
    • Header       — 🧠 SecondSelf + tagline + Refresh graph button
    • Ask your brain — RAG input + answer + sources
    • Knowledge graph — Sub-Phase 4.2 interactive force-directed graph

Architecture references:
  • implementation-plan.md §4.2 (graph component) + §5.2 (Streamlit shell) + §5.3 (pipeline)
  • architecture.md §5.7 (app.py layout)
  • edge-case.md PL-01 / PL-02 (subprocess vs direct calls, stale state)

Run:
    streamlit run app.py
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

import config
from graph_component import load_graph_data, render_in_streamlit

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecondSelf",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens (inlined — clean dark theme matching the reference) ───
_THEME_CSS_PATH = config.PROJECT_ROOT / "static" / "theme.css"
try:
    _THEME_BASE = _THEME_CSS_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    _THEME_BASE = ""

_DESIGN_TOKENS = """
<style>
  :root {
    /* Backgrounds */
    --bg:           #0b0f1a;
    --bg-card:      #141a26;
    --bg-card-hi:   #1a2030;
    --bg-input:     #11161f;
    --sidebar-bg:   #0a0d15;

    /* Text */
    --text:         #e3e6ed;
    --text-strong:  #ffffff;
    --muted:        #8b94a7;
    --faint:        #5a6378;

    /* Borders */
    --border:       #1f2735;
    --border-soft:  #1a2030;

    /* Single accent (coral) — only used on primary action buttons */
    --coral:        #ff4b4b;
    --coral-deep:   #d63838;
    --coral-hi:     #ff6b6b;
    --coral-soft:   rgba(255, 75, 75, 0.18);
    --glow-coral:   0 0 18px rgba(255, 75, 75, 0.35);

    /* Radius / motion */
    --r-sm: 6px;
    --r-md: 10px;
    --t:        180ms ease;
    --t-fast:   120ms ease;

    /* Typography */
    --font-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-body:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono:    'JetBrains Mono', 'Fira Code', Menlo, monospace;
  }
</style>
"""

_APP_CSS = """
<style>
  /* ── Streamlit chrome ─────────────────────────────────────────────── */
  html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text);
  }
  [data-testid="stAppViewContainer"] > .main { position: relative; z-index: 1; }
  [data-testid="stHeader"] { background: transparent; }
  header { visibility: hidden; }
  .block-container { padding-top: 1.6rem; max-width: 1180px; }

  /* ── Sidebar (multi-hue background) ───────────────────────────────── */
  section[data-testid="stSidebar"] {
    background:
      linear-gradient(180deg,
        rgba(28, 14, 36, 0.95) 0%,
        rgba(14, 8, 22, 0.95) 100%),
      radial-gradient(ellipse at top,
        rgba(255, 107, 107, 0.10), transparent 60%);
    border-right: 1px solid var(--border);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.35);
  }
  section[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }
  section[data-testid="stSidebar"] hr { border-color: var(--border-soft); }
  section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: rgba(255, 107, 107, 0.32);
  }

  /* Sidebar titles — clean white, no colored accent bar */
  .ss-sidebar-title {
    font-family: var(--font-display);
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-strong);
    margin: 0 0 10px 0;
    letter-spacing: 0.01em;
  }

  .ss-sidebar-label {
    font-size: 0.7rem;
    color: var(--muted);
    margin: 0 0 6px 0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .ss-divider {
    height: 1px;
    background: var(--border);
    margin: 22px 0;
  }

  /* ── Heading — clean white, matches the reference image ───────────── */
  .ss-header {
    display: flex; align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 32px;
    animation: ss-fade-up 0.5s ease-out;
  }
  .ss-heading {
    font-family: var(--font-display);
    font-size: 3.2rem;
    font-weight: 800;
    margin: 0;
    line-height: 1;
    letter-spacing: -0.03em;
    color: var(--text-strong);
    display: inline-block;
  }
  .ss-tagline {
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 10px;
    font-style: italic;
    font-family: var(--font-display);
  }

  /* ── Section titles — clean white, subtle border, no rainbow ──────── */
  .ss-section-title {
    font-family: var(--font-display);
    font-size: 1.55rem;
    font-weight: 600;
    color: var(--text-strong);
    margin: 30px 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }

  /* ── Buttons — multi-hue system ───────────────────────────────────── */
  .stButton > button {
    border-radius: var(--r-md) !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em;
    transition: background var(--t), border-color var(--t),
                color var(--t), transform var(--t-fast),
                box-shadow var(--t) !important;
  }
  /* Default (ghost) button — neutral with violet hover */
  .stButton > button {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
  }
  .stButton > button:hover {
    background: var(--violet-soft) !important;
    border-color: var(--violet) !important;
    color: var(--violet-hi) !important;
    transform: translateY(-1px);
    box-shadow: var(--glow-violet);
  }
  .stButton > button:active { transform: translateY(0); }
  .stButton > button:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px var(--violet-soft) !important;
  }

  /* Primary action buttons — coral (targeted by their Streamlit key) */
  .st-key-btn_process button,
  .st-key-btn_ask button {
    background: linear-gradient(135deg, var(--coral) 0%, var(--coral-deep) 100%) !important;
    color: #fff !important;
    border: 1px solid var(--coral) !important;
    font-weight: 600 !important;
    box-shadow: var(--glow-coral) !important;
  }
  .st-key-btn_process button:hover,
  .st-key-btn_ask button:hover {
    background: linear-gradient(135deg, var(--coral-hi) 0%, var(--coral) 100%) !important;
    border-color: var(--coral-hi) !important;
    color: #fff !important;
    transform: translateY(-1px);
    box-shadow: 0 0 36px rgba(255, 75, 75, 0.6) !important;
  }

  /* ── Inputs — multi-color focus rings ─────────────────────────────── */
  textarea, input[type="text"], .stTextInput input {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    font-family: var(--font-body) !important;
    transition: border-color var(--t), box-shadow var(--t) !important;
  }
  textarea::placeholder, input::placeholder {
    color: var(--faint) !important;
    font-style: italic;
  }
  textarea:focus, input[type="text"]:focus, .stTextInput input:focus {
    border-color: var(--coral) !important;
    box-shadow: 0 0 0 3px var(--coral-soft) !important;
    outline: none !important;
  }

  /* ── Stats — clean dark cards with white values ───────────────────── */
  .ss-stat-block {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 12px 14px;
    transition: border-color var(--t), background var(--t), transform var(--t-fast);
  }
  .ss-stat-block:hover {
    border-color: var(--border);
    background: var(--bg-card-hi);
    transform: translateY(-2px);
  }
  .ss-stat-label {
    font-size: 0.7rem;
    color: var(--muted);
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .ss-stat-value {
    font-family: var(--font-display);
    font-size: 1.9rem;
    font-weight: 600;
    color: var(--text-strong);
    line-height: 1.1;
  }

  /* ── Checkbox ─────────────────────────────────────────────────────── */
  .stCheckbox label { color: var(--text) !important; }
  .stCheckbox label span { color: var(--muted) !important; }

  /* ── Source expanders ─────────────────────────────────────────────── */
  .streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    color: var(--text) !important;
    transition: border-color var(--t), background var(--t) !important;
  }
  .streamlit-expanderHeader:hover {
    border-color: var(--violet) !important;
    background: var(--bg-card-hi) !important;
  }
  details > div[role="region"] {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--r-md) var(--r-md) !important;
  }

  /* ── Code blocks ──────────────────────────────────────────────────── */
  code, pre, .stCodeBlock {
    font-family: var(--font-mono) !important;
    background: var(--bg-input) !important;
    color: var(--gold) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
  }
  pre code { background: transparent !important; border: none !important; }

  /* ── Alerts ───────────────────────────────────────────────────────── */
  .stAlert {
    border-radius: var(--r-md) !important;
    border-left: 3px solid var(--coral) !important;
  }
  [data-baseweb="notification"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
  }

  /* ── Toasts (capture flash) ──────────────────────────────────────── */
  [data-testid="stToast"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--emerald) !important;
    color: var(--text) !important;
    border-radius: var(--r-md) !important;
    box-shadow: var(--glow-emerald) !important;
  }

  /* ── Hide Streamlit branding ──────────────────────────────────────── */
  #MainMenu, footer, .viewerBadge_link__qRIco { display: none !important; }

  /* ── Responsive tweaks ───────────────────────────────────────────── */
  @media (max-width: 768px) {
    .ss-heading { font-size: 2.2rem; }
    .block-container { padding-top: 1rem; padding-left: 0.8rem; padding-right: 0.8rem; }
  }
</style>
"""
st.markdown(_DESIGN_TOKENS + _THEME_BASE + _APP_CSS, unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _count_wiki_notes() -> int:
    """Count all *.md files under wiki/."""
    if not config.WIKI_DIR.exists():
        return 0
    return sum(1 for _ in config.WIKI_DIR.rglob("*.md"))


def _graph_counts() -> tuple[int, int]:
    """Return (node_count, edge_count) from graph.json, tolerant of missing file."""
    data = load_graph_data()
    meta = data.get("meta") or {}
    nodes = meta.get("note_count", len(data.get("nodes", [])))
    edges = meta.get("edge_count", len(data.get("edges", [])))
    return int(nodes), int(edges)


@contextlib.contextmanager
def _capture_stdout():
    """Redirect Python-level stdout (used by pipeline scripts' prints)."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        yield buf
    finally:
        sys.stdout = old


def _run_pipeline(force: bool) -> tuple[bool, str]:
    """
    Run classify → link → build_graph in-process, capturing their print() output.

    Returns (success, combined_output).  `force` maps to `classify --force`
    per docs/implementation-plan.md §2.
    """
    sections: list[str] = []
    ok = True
    try:
        # ── classify ──────────────────────────────────────────────────
        sections.append("── Classify ─────────────────────────────────────────")
        with _capture_stdout() as buf:
            import classify
            old_argv = sys.argv
            sys.argv = ["classify.py"]
            if force:
                sys.argv.append("--force")
            try:
                classify.main()
            finally:
                sys.argv = old_argv
        sections.append(buf.getvalue() or "(no output)")

        # ── link ──────────────────────────────────────────────────────
        sections.append("\n── Link ─────────────────────────────────────────────")
        with _capture_stdout() as buf:
            import link
            old_argv = sys.argv
            sys.argv = ["link.py"]
            try:
                link.main()
            finally:
                sys.argv = old_argv
        sections.append(buf.getvalue() or "(no output)")

        # ── build_graph ───────────────────────────────────────────────
        sections.append("\n── Build graph ──────────────────────────────────────")
        with _capture_stdout() as buf:
            import build_graph
            old_argv = sys.argv
            sys.argv = ["build_graph.py"]
            try:
                build_graph.main()
            finally:
                sys.argv = old_argv
        sections.append(buf.getvalue() or "(no output)")

    except SystemExit as exc:
        ok = (exc.code in (None, 0))
        sections.append(f"\n[exited with code {exc.code}]")
    except Exception as exc:  # noqa: BLE001 — surface any pipeline failure
        ok = False
        sections.append(f"\n[error] {type(exc).__name__}: {exc}")

    return ok, "\n".join(sections)


def _write_note_capture(text: str) -> dict[str, Any]:
    """Write a note envelope to raw/{id}.json (architecture §4.1)."""
    config.ensure_project_dirs()
    capture = {
        "id": _new_id(),
        "captured_at": _now_iso(),
        "source_type": "note",
        "content": text.strip(),
        "metadata": {},
    }
    raw_path = config.RAW_DIR / f"{capture['id']}.json"
    raw_path.write_text(
        json.dumps(capture, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {"id": capture["id"], "path": str(raw_path)}


# ── Sidebar: Capture ────────────────────────────────────────────────────────

def render_capture_section() -> None:
    st.markdown(
        '<p class="ss-sidebar-title">Capture</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<p class="ss-sidebar-label">Quick note</p>', unsafe_allow_html=True)
    note_text = st.text_area(
        "Quick note",
        value=st.session_state.get("capture_text", ""),
        placeholder="Capture a thought, task, or insight…",
        height=110,
        label_visibility="collapsed",
        key="capture_textarea",
    )
    if st.button("Capture note", use_container_width=True, key="btn_capture"):
        text = (note_text or "").strip()
        if not text:
            st.warning("Type something to capture first.")
            return
        try:
            result = _write_note_capture(text)
            st.success(f"Captured → {result['id'][:8]}")
            st.session_state["capture_text"] = ""
            st.session_state["capture_flash"] = (
                f"✅ Saved `{result['id'][:8]}` to `raw/`. "
                "Run the pipeline below to classify and link it."
            )
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Capture failed: {exc}")


# ── Sidebar: Pipeline ───────────────────────────────────────────────────────

def render_pipeline_section() -> None:
    st.markdown('<div class="ss-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ss-sidebar-title">Pipeline</p>',
        unsafe_allow_html=True,
    )
    force = st.checkbox(
        "Force re-process",
        value=st.session_state.get("force_reprocess", False),
        key="force_reprocess",
        help="Re-classify every raw item, ignoring the dedup index.",
    )

    btn = st.button(
        "Process new captures",
        use_container_width=True,
        key="btn_process",
    )
    if btn:
        with st.spinner("Running classify → link → build_graph…"):
            ok, output = _run_pipeline(force=force)
        st.session_state["pipeline_output"] = output
        st.session_state["pipeline_ok"] = ok
        if ok:
            st.success("Pipeline finished. Graph is up to date.")
        else:
            st.error("Pipeline finished with errors. See details below.")
        st.rerun()

    if st.session_state.get("pipeline_output"):
        with st.expander("Pipeline log", expanded=not st.session_state.get("pipeline_ok", True)):
            st.code(st.session_state["pipeline_output"], language="bash")


# ── Sidebar: Stats ───────────────────────────────────────────────────────────

def render_stats_section() -> None:
    st.markdown('<div class="ss-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ss-sidebar-title">Stats</p>',
        unsafe_allow_html=True,
    )
    wiki = _count_wiki_notes()
    nodes, edges = _graph_counts()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="ss-stat-block">'
            f'<p class="ss-stat-label">Wiki notes</p>'
            f'<p class="ss-stat-value">{wiki}</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="ss-stat-block">'
            f'<p class="ss-stat-label">Graph nodes</p>'
            f'<p class="ss-stat-value">{nodes}</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="ss-stat-block">'
            f'<p class="ss-stat-label">Graph edges</p>'
            f'<p class="ss-stat-value">{edges}</p>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── Main: header ────────────────────────────────────────────────────────────

def render_header() -> None:
    cols = st.columns([6, 1])
    with cols[0]:
        st.markdown(
            '<h1 class="ss-heading">🧠 SecondSelf</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="ss-tagline">Your personal AI second brain — '
            'capture, organize, explore, ask.</p>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        if st.button("Refresh graph", key="btn_refresh", use_container_width=True):
            st.session_state["graph_cache_bust"] = (
                st.session_state.get("graph_cache_bust", 0) + 1
            )
            st.rerun()


# ── Main: Ask your brain ────────────────────────────────────────────────────

def render_ask_section() -> None:
    st.markdown('<p class="ss-section-title">Ask your brain</p>', unsafe_allow_html=True)

    defaults = st.session_state.get("ask_question", "What are my career goals?")
    question = st.text_input(
        "Ask a question",
        value=defaults,
        placeholder="What are my career goals?",
        label_visibility="collapsed",
        key="ask_input",
    )

    ask_cols = st.columns([6, 1])
    with ask_cols[1]:
        ask_clicked = st.button(
            "Ask",
            key="btn_ask",
            use_container_width=True,
        )

    if ask_clicked:
        q = (question or "").strip()
        if not q:
            st.warning("Type a question first.")
            return
        with st.spinner("Searching your brain…"):
            try:
                from ask import ask as ask_brain
                result = ask_brain(q)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Ask failed: {exc}")
                return
        st.session_state["ask_result"] = result
        st.session_state["ask_question"] = q

    result = st.session_state.get("ask_result")
    if result:
        st.markdown("---")
        st.markdown(result.get("answer", ""))
        sources = result.get("sources") or []
        if sources:
            st.markdown("**Sources**")
            for src in sources:
                title = src.get("title") or src.get("slug") or src.get("id")
                path = src.get("path", "")
                score = src.get("relevance_score")
                score_str = f" — score {score:.3f}" if isinstance(score, (int, float)) else ""
                with st.expander(f"{title}{score_str}"):
                    st.markdown(f"**Path:** `{path}`")
                    st.markdown(f"**PARA:** `{src.get('para', '')}`")
                    if src.get("summary"):
                        st.markdown(f"**Summary:** {src['summary']}")


# ── Main: Knowledge graph ──────────────────────────────────────────────────

def render_knowledge_graph() -> None:
    st.markdown(
        '<p class="ss-section-title">Knowledge graph</p>',
        unsafe_allow_html=True,
    )
    # The Sub-Phase 4.2 component handles missing/empty state internally.
    render_in_streamlit()


# ── Main: layout ────────────────────────────────────────────────────────────

def render_main() -> None:
    render_header()
    render_ask_section()
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    render_knowledge_graph()


# ── Entry point ─────────────────────────────────────────────────────────────

def main() -> None:
    # Initialise session-state defaults so widgets stay stable across reruns.
    st.session_state.setdefault("capture_text", "")
    st.session_state.setdefault("force_reprocess", False)
    st.session_state.setdefault("ask_question", "What are my career goals?")
    st.session_state.setdefault("ask_result", None)
    st.session_state.setdefault("pipeline_output", "")
    st.session_state.setdefault("pipeline_ok", True)
    st.session_state.setdefault("graph_cache_bust", 0)

    # Show a flash banner after a successful capture.
    flash = st.session_state.pop("capture_flash", None)
    if flash:
        st.toast(flash, icon="✅")

    with st.sidebar:
        render_capture_section()
        render_pipeline_section()
        render_stats_section()

    render_main()


# Streamlit runs `app.py` as the main script.  Calling `main()` at
# module level is the standard Streamlit convention and works correctly
# with the framework's rerun model.
main()
