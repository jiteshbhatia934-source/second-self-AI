---
kind: dependency_management
name: Python Dependency Management via requirements.txt and .env
category: dependency_management
scope:
    - '**'
source_files:
    - requirements.txt
    - .env.example
    - config.py
---

This repository uses a straightforward Python dependency management approach centered on a single `requirements.txt` file with pinned versions, alongside environment-based configuration through `.env` files.

**System/Approach:**
- Dependencies are declared in `requirements.txt` using exact version pinning (e.g., `streamlit==1.45.1`, `groq==0.28.0`, `sentence-transformers==4.1.0`, `torch==2.13.0`). No lockfile (`requirements.lock`, `poetry.lock`, etc.) is present.
- A local virtual environment directory `.venv/` exists but appears empty/unpopulated in the snapshot — dependencies are not vendored into the repo.
- Configuration secrets and runtime options are managed via `.env` files loaded through `python-dotenv`, with an `.env.example` template provided for reference.

**Key Files:**
- `requirements.txt` — sole source of third-party dependency declarations with pinned versions
- `.env.example` — template for required/optional environment variables (GROQ_API_KEY, path overrides, thresholds)
- `config.py` — central configuration loader that reads `.env` via `dotenv.load_dotenv()` and validates typed environment variables with bounds checking

**Architecture & Conventions:**
- All CLI scripts (`ask.py`, `build_graph.py`, `capture.py`, `classify.py`, `link.py`, `pipeline.py`) import from the local `lib/` package and standard library modules only — no additional imports beyond what's listed in `requirements.txt`.
- Optional dependencies are handled gracefully: `python-dotenv` is wrapped in a try/except fallback so core code can run without it installed (Phase 1 compatibility).
- Environment variables are strongly typed and validated at load time (float/int ranges enforced via `_float_env` and `_int_env` helpers), ensuring misconfiguration fails fast.

**Conventions & Constraints:**
- Exact version pinning is used consistently across all dependencies — no range specifiers or `>=` constraints.
- Secrets (like `GROQ_API_KEY`) must never be committed; `.env` is explicitly excluded via `.gitignore` convention shown in `.env.example` comments.
- No private PyPI registry, vendoring, or dependency update automation is configured in this snapshot.