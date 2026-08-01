#!/usr/bin/env python3
"""
pipeline.py — orchestrate classify → link → build_graph

Usage:
  python pipeline.py classify    # classify only (raw → wiki)
  python pipeline.py link        # link only (wiki → embeddings + wikilinks)
  python pipeline.py process     # classify + link + rebuild graph
"""
from __future__ import annotations

import sys


def _run_classify() -> None:
    print("── Classify ─────────────────────────────────────────")
    import classify
    classify.main()


def _run_link() -> None:
    print("── Link ─────────────────────────────────────────────")
    import link
    link.main()


def _run_graph() -> None:
    print("── Build graph ──────────────────────────────────────")
    import build_graph
    build_graph.main()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py classify | link | process")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "classify":
        _run_classify()
    elif cmd == "link":
        _run_link()
    elif cmd == "process":
        _run_classify()
        _run_link()
        _run_graph()
    else:
        print(f"Unknown command: {cmd!r}")
        print("Usage: python pipeline.py classify | link | process")
        sys.exit(1)


if __name__ == "__main__":
    main()
