---
kind: error_handling
name: Python Exception Handling and CLI Exit Patterns
category: error_handling
scope:
    - '**'
source_files:
    - capture.py
    - classify.py
    - ask.py
    - build_graph.py
---

This repository uses Python's built-in exception handling with a consistent pattern across all CLI tools. There is no centralized error type hierarchy or custom exception classes — instead, the codebase relies on broad `except Exception` blocks with graceful degradation and user-friendly messaging.

**Core patterns observed:**

1. **Broad exception swallowing for resilience**: Most I/O operations (file reading, JSON parsing, network requests) are wrapped in `try/except Exception` blocks that log errors to stderr and continue processing rather than failing the entire pipeline. Examples include `classify.py`'s `read_raw_records()` which skips malformed JSON files, and `build_graph.py`'s `_read_notes_from()` which ignores unreadable markdown files.

2. **Typer CLI exit codes**: The `capture.py` tool uses `typer.Exit(code=1)` for validation failures (missing files, invalid paths) combined with colored error messages via `typer.secho(..., fg=typer.colors.RED, err=True)`. This provides consistent CLI error signaling.

3. **Graceful fallbacks over exceptions**: Network operations use optional imports (`import httpx` inside try blocks) and return None on failure rather than raising exceptions. LLM calls wrap API calls in retry loops with fallback to local heuristics when external services fail.

4. **Best-effort atomic writes**: File operations use try/except blocks around critical sections like graph building, where failed index updates don't prevent the main operation from completing.

5. **No custom exception types**: The codebase doesn't define custom exception classes. All errors propagate as standard Python exceptions or are caught and handled inline.

6. **Structured error responses**: The `ask.py` module returns structured `AskResult` dataclasses with meaningful default messages for various error conditions (empty questions, missing wiki notes, unconfigured LLM, low relevance scores).

**Key conventions:**
- Print error messages to stderr using `print(..., file=sys.stderr)`
- Use `continue` to skip problematic items in batch processing
- Return None or empty results for non-fatal failures
- Validate inputs early and exit with appropriate status codes
- Never let external service failures crash the entire pipeline