from __future__ import annotations

import json
import mimetypes
import re
import shutil
import uuid
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import typer

import config

app = typer.Typer(help="Capture notes, links, and files into raw storage.")


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _new_id() -> str:
    return uuid.uuid4().hex


def _write_capture(capture: dict[str, Any]) -> Path:
    config.ensure_project_dirs()
    raw_path = config.RAW_DIR / f"{capture['id']}.json"
    with raw_path.open("w", encoding="utf-8") as handle:
        json.dump(capture, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return raw_path


def _fetch_url_title(url: str) -> str | None:
    try:
        # Import httpx lazily so that capture.py still works even if httpx is not installed.
        # Fetching the title is optional — returning None will make the caller fall back to the URL.
        try:
            import httpx  # type: ignore
        except ImportError:
            return None

        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            parser = TitleParser()
            parser.feed(response.text)
            title = parser.title.strip()
            return title or None
    except Exception:
        return None


@app.command("note")
def capture_note(text: str) -> None:
    """Capture a text note into raw storage."""
    capture = {
        "id": _new_id(),
        "captured_at": _now_iso(),
        "source_type": "note",
        "content": text.strip(),
        "metadata": {},
    }
    raw_path = _write_capture(capture)
    typer.echo(f"Captured note: {capture['id']}")
    typer.echo(raw_path)


@app.command("link")
def capture_link(url: str) -> None:
    """Capture a web link into raw storage."""
    metadata: dict[str, Any] = {"url": url}
    content = ""
    title = _fetch_url_title(url)
    if title:
        content = title
    else:
        content = url
    capture = {
        "id": _new_id(),
        "captured_at": _now_iso(),
        "source_type": "link",
        "content": content,
        "metadata": metadata,
    }
    raw_path = _write_capture(capture)
    typer.echo(f"Captured link: {capture['id']}")
    typer.echo(raw_path)


@app.command("file")
def capture_file(path: Path) -> None:
    """Capture a local file into raw storage."""
    if not path.exists():
        typer.secho(f"File not found: {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if not path.is_file():
        typer.secho(f"Not a file: {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    capture_id = _new_id()
    config.ensure_project_dirs()
    file_dir = config.RAW_DIR / "files" / capture_id
    file_dir.mkdir(parents=True, exist_ok=True)

    target_path = file_dir / path.name
    try:
        shutil.copy2(path, target_path)
    except Exception as exc:
        typer.secho(f"Failed to copy file: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    mime_type, _ = mimetypes.guess_type(path)
    metadata: dict[str, Any] = {
        "original_filename": path.name,
        "mime_type": mime_type or "application/octet-stream",
        "file_path_ref": str(target_path.relative_to(config.PROJECT_ROOT).as_posix()),
    }

    content = ""
    if path.suffix.lower() in {".txt", ".md"}:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = ""

    capture = {
        "id": capture_id,
        "captured_at": _now_iso(),
        "source_type": "file",
        "content": content,
        "metadata": metadata,
    }
    raw_path = _write_capture(capture)
    typer.echo(f"Captured file: {capture_id}")
    typer.echo(raw_path)


if __name__ == "__main__":
    app()
