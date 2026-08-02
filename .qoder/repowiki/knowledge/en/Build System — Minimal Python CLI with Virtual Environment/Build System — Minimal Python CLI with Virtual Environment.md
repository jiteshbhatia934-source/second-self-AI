---
kind: build_system
name: Build System — Minimal Python CLI with Virtual Environment
category: build_system
scope:
    - '**'
source_files:
    - requirements.txt
    - .env.example
    - config.py
    - README.md
---

This repository does not implement a formal build system. There is no Makefile, Dockerfile, CI pipeline, packaging script (setup.py/pyproject.toml), or automated test runner present in the codebase. The project is a Python 3.10+ CLI application whose "build" consists of installing dependencies into a local virtual environment and running Python scripts directly.

**What is used**
- **Dependency management**: `requirements.txt` pins exact versions for all runtime packages (streamlit, groq, sentence-transformers, torch, PyYAML, python-frontmatter, numpy, httpx, python-dotenv, typer).
- **Environment configuration**: `.env.example` documents required/optional variables; `python-dotenv` loads them at runtime via `config.py`. Secrets are intentionally excluded from version control.
- **Execution model**: Each phase is a standalone Python script (`capture.py`, `classify.py`, `link.py`, `build_graph.py`, `graph_preview.py`, `ask.py`, `pipeline.py`) invoked directly with `python <script>.py`. No wrapper shell scripts or Make targets exist.
- **Virtual environment**: Users create an isolated `.venv` and install with `python -m pip install -r requirements.txt`.

**Key files**
- `requirements.txt` — single source of truth for dependencies
- `.env.example` — documented environment variable contract
- `config.py` — runtime config loader that validates defaults and rejects invalid values at startup
- `README.md` — setup instructions and workflow commands

**Architecture & conventions**
- Scripts are stateless entry points that read/write to well-known directories (`raw/`, `wiki/`, `data/`, `graph.json`).
- Configuration is centralized in `config.py` and loaded via dotenv; relative paths resolve against the repository root.
- The planned workflow is a linear pipeline: capture → classify → link → graph → preview → ask, executed by chaining the individual scripts.

**Conventions & constraints**
- Python 3.10+ is required (stated in README and implied by dependency versions).
- `.env` must never be committed; it is gitignored.
- All dependency versions are pinned to exact releases — there is no loose version resolution.
- Tests are only mentioned as a future plan in `docs/implementation-plan.md` and `docs/edge-case.md`; no `tests/` directory or pytest configuration exists yet.
- No containerization, cross-compilation, or release automation is present.