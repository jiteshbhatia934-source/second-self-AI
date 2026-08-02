---
kind: external_dependency
name: vis-network JavaScript library for the force-directed graph
slug: vis-network
category: external_dependency
category_hints:
    - framework_behavior
scope:
    - '**'
source_files:
    - static/graph.html
    - README.md
---

### vis-network
- Role: Browser-side library rendering `graph.json` nodes/edges as an interactive force-directed graph with drag, zoom, pan, and hover tooltips.
- Integration point: Embedded via `static/graph.html`, loaded through Streamlit's `st.components.v1.html`. Reads root `graph.json` first, falls back to `data/graph.json` for backward compatibility.
- Usage model: Force-directed physics layout; node color coded by PARA category; tooltip shows title, summary, and body snippet.