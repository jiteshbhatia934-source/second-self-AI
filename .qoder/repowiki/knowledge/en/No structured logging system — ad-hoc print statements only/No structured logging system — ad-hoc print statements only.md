---
kind: logging_system
name: No structured logging system — ad-hoc print statements only
category: logging_system
scope:
    - '**'
source_files:
    - ask.py
    - build_graph.py
    - classify.py
    - link.py
    - lib/embeddings.py
    - lib/extract.py
    - lib/llm.py
---

This repository does not implement a logging system. There is no use of Python's `logging` module, nor any third-party logging library (e.g., loguru, structlog, sentry). All diagnostic output is produced via bare `print()` calls scattered across the CLI scripts (`ask.py`, `build_graph.py`, `classify.py`, `link.py`) and core library modules (`lib/embeddings.py`, `lib/extract.py`, `lib/llm.py`). These prints serve as informal progress/error messages and are written to stdout or stderr depending on context; there is no centralized logger configuration, no log levels, no structured fields, and no sinks or file rotation. Error paths consistently write to `sys.stderr` via `file=sys.stderr`, while informational messages go to stdout. The absence of any logging framework initialization, configuration files, or dedicated logging modules means this project has no formal logging architecture.