"""
lib/extract.py — text extraction helpers for each capture source type.

Provides:
  extract_text(capture_meta_dict) → str
    Dispatches by type: note → read content.md
                        link → requests + BS4 strip, fallback URL string
                        file → pypdf text, fallback filename
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict


def extract_text(capture: Dict[str, Any]) -> str:
    """
    Extract plain text from a raw capture record (as returned by read_raw_captures).
    capture must have keys: type, source, _content_path.
    """
    ctype: str = str(capture.get("type", "note")).lower()
    content_path: str | None = capture.get("_content_path")

    if ctype == "note":
        return _read_text_file(content_path) or str(capture.get("source", ""))

    if ctype == "link":
        return _fetch_link(str(capture.get("source", "")), content_path)

    if ctype == "file":
        return _extract_file(content_path, str(capture.get("original_filename", "")))

    # Unknown type — fall back to whatever text we have
    return _read_text_file(content_path) or str(capture.get("source", ""))


# ── Note ──────────────────────────────────────────────────────────────────────

def _read_text_file(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


# ── Link ──────────────────────────────────────────────────────────────────────

def _fetch_link(url: str, content_path: str | None) -> str:
    """
    Fetch URL with requests + BeautifulSoup; fall back to stored content or URL.
    Respects a 10-second timeout and max 5 redirects.
    """
    # Try stored content first (already fetched at capture time)
    stored = _read_text_file(content_path)
    if stored:
        return stored

    if not url:
        return ""

    try:
        import requests  # type: ignore
        from bs4 import BeautifulSoup  # type: ignore

        resp = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "SecondSelf/1.0 (+https://github.com/secondself)"},
            max_redirects=5,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:8000]   # cap to avoid context overflow
    except Exception as exc:
        print(f"[extract] Link fetch failed ({url}): {exc}", file=sys.stderr)
        return url   # store the URL itself as fallback content


# ── File ─────────────────────────────────────────────────────────────────────

def _extract_file(content_path: str | None, original_filename: str = "") -> str:
    """
    Extract text from a captured file.
    Supports: .pdf (pypdf), .md/.txt/.rst (plain read), others (filename fallback).
    """
    if not content_path:
        return original_filename or ""

    p = Path(content_path)
    if not p.exists():
        return original_filename or str(p.name)

    suffix = p.suffix.lower()

    # PDF
    if suffix == ".pdf":
        return _extract_pdf(p) or original_filename or str(p.name)

    # Plain text
    if suffix in {".md", ".txt", ".rst", ".csv", ".json", ".yaml", ".yml"}:
        return _read_text_file(str(p))

    # Binary / unknown — return filename only
    return original_filename or str(p.name)


def _extract_pdf(path: Path) -> str:
    """Extract text from a PDF using pypdf; returns empty string on failure."""
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(pages).strip()[:8000]
    except Exception as exc:
        print(f"[extract] PDF extraction failed ({path.name}): {exc}", file=sys.stderr)
        return ""
