---
kind: configuration_system
name: SecondSelf Configuration System
category: configuration_system
scope:
    - '**'
source_files:
    - config.py
    - .env.example
    - requirements.txt
    - capture.py
    - classify.py
    - build_graph.py
    - ask.py
---

SecondSelf uses a lightweight, environment-driven configuration system centered on a single `config.py` module that loads `.env` files via `python-dotenv` and exposes typed accessors for all runtime settings. The system follows a clear hierarchy: explicit environment variables override defaults, with path values resolved relative to the project root when not absolute.

**Core mechanism**
- `config.py` is imported by every CLI tool (`capture.py`, `classify.py`, `build_graph.py`, `ask.py`, etc.) and serves as the single source of truth for paths, model settings, and feature toggles.
- `.env` loading is wrapped in a try/except so the code runs even if `python-dotenv` is missing (Phase 1 fallback), though it is listed in `requirements.txt`.
- Path resolution helper `_path_from_env()` accepts an env key and a default relative path; if the env var is set but not absolute, it resolves against `PROJECT_ROOT`.
- Typed helpers `_float_env()` and `_int_env()` validate ranges at load time, raising `ValueError` with descriptive messages for out-of-range or non-numeric values.

**Configuration keys**
- **Paths**: `RAW_DIR`, `WIKI_DIR`, `DATA_DIR`, `GRAPH_PATH` — all default to project-relative locations (`raw/`, `wiki/`, `data/`, `graph.json`).
- **LLM/embedding**: `GROQ_API_KEY` (required for classify/ask phases), `EMBEDDING_MODEL` (defaults to `all-MiniLM-L6-v2`, must be non-empty).
- **Tuning**: `SIMILARITY_THRESHOLD` (0.0–1.0, default 0.80), `TOP_K_RETRIEVAL` (1–20, default 8).
- **PARA structure**: `PARA_FOLDERS = ("Projects", "Areas", "Resources", "Archives")` enforces the wiki taxonomy.
- **Feature gate**: `groq_configured()` returns whether `GROQ_API_KEY` is set, used throughout the codebase to fall back to local heuristics.

**Directory bootstrapping**
- `ensure_project_dirs()` creates all expected directories on first use, including PARA subfolders under `WIKI_DIR`. This is called early in each CLI entry point so the filesystem is ready before any I/O.

**Conventions and constraints**
- All configuration lives in one module; no YAML/TOML/JSON config files are read at runtime.
- Secrets (`GROQ_API_KEY`) come exclusively from environment variables (`.env` file or shell), never from code.
- `.env.example` documents every supported variable with defaults and comments; `.env` itself is gitignored.
- Invalid numeric values or empty required strings raise `ValueError` immediately at import/config-load time rather than failing later during processing.