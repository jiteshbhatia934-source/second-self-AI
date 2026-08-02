#!/usr/bin/env python3
"""
dedupe_resources.py — remove duplicate notes from wiki/Resources/.

Detects groups of files matching the pattern `<base>(-N)?.md` where N is
one or more digits, e.g.

    deep-work-summary.md
    deep-work-summary-1.md
    deep-work-summary-2.md
    deep-work-summary-3.md

For each group with > 1 file:
  1. Pick a **canonical** file (longest body; bare-named wins ties; file
     with valid front-matter beats a stub).
  2. Rewrite every wikilink `[[removed-slug]]` across the entire `wiki/`
     to point to the canonical slug.
  3. Delete the non-canonical files.

Default mode is **dry-run** — prints the plan without touching anything.
Use `--apply` to actually delete and rewrite.  `--rebuild-graph` runs
`build_graph.py` afterwards so `graph.json` and the Streamlit app reflect
the cleaned-up wiki.

Why this exists
---------------
Repeated `classify.py --force` runs and link-bot iterations created
`-1`, `-2`, ... siblings of notes that already exist (e.g. the
"Deep Work Summary" group has six copies of the same content).  This
script is the deterministic, reviewable way to collapse them back to
one canonical note per concept.

Usage
-----
    python dedupe_resources.py                # dry-run
    python dedupe_resources.py --apply        # actually delete + rewrite
    python dedupe_resources.py --apply --rebuild-graph
    python dedupe_resources.py --verbose      # show full plan
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import config

# ── Constants ──────────────────────────────────────────────────────────────
RESOURCES_DIR: Path = config.WIKI_DIR / "Resources"
WIKI_DIR: Path = config.WIKI_DIR

# Matches `<base>.md` or `<base>-<digits>.md` (digits only — `weekly-review-1` yes,
# `weekly-review-idea-1` no because the suffix after the dash is not pure digits).
_NUM_SUFFIX_RE = re.compile(r"^(?P<base>.+)-(?P<n>\d+)$")
_WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.S)


# ── Data model ─────────────────────────────────────────────────────────────

@dataclass
class NoteFile:
    """Lightweight representation of a single wiki .md file."""
    path: Path
    slug: str                       # filename without .md
    body: str                       # full text
    body_no_fm: str                 # text with front matter stripped
    has_frontmatter: bool

    @property
    def size(self) -> int:
        return len(self.body_no_fm.strip())


@dataclass
class DedupeGroup:
    base: str                       # canonical-slug base name
    files: list[NoteFile] = field(default_factory=list)
    canonical: NoteFile | None = None
    duplicates: list[NoteFile] = field(default_factory=list)


# ── File loading ───────────────────────────────────────────────────────────

def _read(path: Path) -> NoteFile:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = _FRONTMATTER_RE.match(text)
    if m:
        body = text[m.end():].lstrip("\n")
        has_fm = True
    else:
        body = text
        has_fm = False
    return NoteFile(
        path=path,
        slug=path.stem,
        body=text,
        body_no_fm=body,
        has_frontmatter=has_fm,
    )


def _group_by_base(files: Iterable[NoteFile]) -> dict[str, DedupeGroup]:
    """Group files by their shared base name.

    A file named `foo.md` becomes base `foo`.
    A file named `foo-3.md` becomes base `foo` and joins the same group.
    """
    groups: dict[str, DedupeGroup] = {}
    for nf in files:
        m = _NUM_SUFFIX_RE.match(nf.slug)
        base = m.group("base") if m else nf.slug
        groups.setdefault(base, DedupeGroup(base=base)).files.append(nf)
    return groups


# ── Canonical selection ────────────────────────────────────────────────────

def _pick_canonical(group: DedupeGroup) -> NoteFile:
    """Choose which file in the group survives.

    Priority (highest first):
      1. File with valid front matter AND largest body
      2. Bare-named file (`foo.md` over `foo-1.md`, `foo-2.md`, ...)
      3. Otherwise the file with the largest body
    """
    files = group.files
    if not files:
        raise ValueError("empty group")

    # Sort key: (has_frontmatter desc, body_size desc, is_bare desc)
    def key(nf: NoteFile) -> tuple[int, int, int]:
        return (
            1 if nf.has_frontmatter else 0,
            nf.size,
            1 if nf.slug == group.base else 0,
        )

    return sorted(files, key=key, reverse=True)[0]


# ── Wikilink rewriting ─────────────────────────────────────────────────────

@dataclass
class Rewrite:
    file: Path
    line_no: int
    old_target: str
    new_target: str


def _find_rewrites(wiki_dir: Path, removed_slugs: set[str], canonical_map: dict[str, str]) -> list[Rewrite]:
    """Scan every .md under wiki_dir for `[[removed]]` and plan rewrites."""
    rewrites: list[Rewrite] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for m in _WIKILINK_RE.finditer(line):
                target = m.group(1).strip()
                if target in removed_slugs:
                    new_target = canonical_map[target]
                    if new_target != target:
                        rewrites.append(Rewrite(file=path, line_no=i,
                                                old_target=target, new_target=new_target))
    return rewrites


def _apply_rewrites(rewrites: list[Rewrite]) -> int:
    """Apply rewrites in-place across files.  Returns number of files touched."""
    by_file: dict[Path, list[Rewrite]] = defaultdict(list)
    for r in rewrites:
        by_file[r.file].append(r)

    touched = 0
    for path, items in by_file.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        # group by line, then replace in stable order
        by_line: dict[int, list[Rewrite]] = defaultdict(list)
        for r in items:
            by_line[r.line_no].append(r)

        new_lines = []
        for i, line in enumerate(text.splitlines(), start=1):
            if i in by_line:
                # Replace every [[old]] -> [[new]] on this line, preserving formatting
                # by re-running the regex
                def _sub(match: re.Match) -> str:
                    target = match.group(1).strip()
                    if target in {r.old_target for r in by_line[i]}:
                        new = next(r.new_target for r in by_line[i] if r.old_target == target)
                        return match.group(0).replace(target, new)
                    return match.group(0)
                line = _WIKILINK_RE.sub(_sub, line)
            new_lines.append(line)

        new_text = "\n".join(new_lines)
        if not new_text.endswith("\n"):
            new_text += "\n"
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            touched += 1
    return touched


# ── Plan printing ──────────────────────────────────────────────────────────

def _print_plan(groups: list[DedupeGroup], rewrites: list[Rewrite], verbose: bool = False) -> None:
    if not groups:
        print("No duplicate groups found in wiki/Resources/.")
        return
    print(f"Found {len(groups)} duplicate group(s) in wiki/Resources/:\n")
    total_to_delete = 0
    for g in groups:
        if g.canonical is None or len(g.files) < 2:
            continue
        kept = g.canonical
        removed = g.duplicates
        total_to_delete += len(removed)
        print(f"  base: {g.base}")
        print(f"    KEEP     {kept.path.name}  ({kept.size} chars, fm={kept.has_frontmatter})")
        for r in removed:
            print(f"    DELETE   {r.path.name}  ({r.size} chars, fm={r.has_frontmatter})")
    print(f"\nTotal files to delete: {total_to_delete}")
    print(f"Wikilink rewrites planned: {len(rewrites)}")
    if rewrites and verbose:
        print("\nRewrites:")
        for r in rewrites:
            print(f"    {r.file.relative_to(WIKI_DIR)}:{r.line_no}  [[{r.old_target}]] -> [[{r.new_target}]]")


# ── Main ───────────────────────────────────────────────────────────────────

def _iter_resource_files() -> list[NoteFile]:
    if not RESOURCES_DIR.exists():
        return []
    return [_read(p) for p in sorted(RESOURCES_DIR.glob("*.md"))]


def _select_duplicates(groups: dict[str, DedupeGroup]) -> list[DedupeGroup]:
    """Annotate each group with its canonical and duplicates (only multi-file groups)."""
    out: list[DedupeGroup] = []
    for base, g in groups.items():
        if len(g.files) < 2:
            continue
        g.canonical = _pick_canonical(g)
        g.duplicates = [f for f in g.files if f is not g.canonical]
        out.append(g)
    return sorted(out, key=lambda g: g.base)


def _build_canonical_map(groups: list[DedupeGroup]) -> tuple[set[str], dict[str, str], list[Path]]:
    """Return (removed_slugs, {removed -> canonical}, [paths to delete])."""
    removed: set[str] = set()
    cmap: dict[str, str] = {}
    delete_paths: list[Path] = []
    for g in groups:
        canonical_slug = g.canonical.slug
        for d in g.duplicates:
            removed.add(d.slug)
            cmap[d.slug] = canonical_slug
            delete_paths.append(d.path)
    return removed, cmap, delete_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true",
                        help="Actually delete files and rewrite wikilinks (default: dry-run).")
    parser.add_argument("--verbose", action="store_true", help="Show full rewrite plan in dry-run.")
    parser.add_argument("--rebuild-graph", action="store_true",
                        help="After dedupe, run build_graph.py to refresh graph.json.")
    parser.add_argument("--purge-embeddings", action="store_true",
                        help="Drop entries for deleted slugs from data/embeddings.pkl.")
    args = parser.parse_args(argv)

    # 1. Load & group
    files = _iter_resource_files()
    groups = _select_duplicates(_group_by_base(files))

    if not groups:
        print("No duplicates found in wiki/Resources/.")
        return 0

    # 2. Plan wikilink rewrites
    removed, cmap, delete_paths = _build_canonical_map(groups)
    rewrites = _find_rewrites(WIKI_DIR, removed, cmap)

    # 3. Show plan
    _print_plan(groups, rewrites, verbose=args.verbose)

    if not args.apply:
        print("\nDry run only — re-run with --apply to delete + rewrite.")
        return 0

    # 4. Apply rewrites first (so deleted files aren't referenced)
    print("\nRewriting wikilinks...")
    touched = _apply_rewrites(rewrites)
    print(f"  -> rewrote wikilinks in {touched} file(s).")

    # 5. Optionally purge embedding cache for removed slugs
    purged = 0
    if args.purge_embeddings:
        emb_path = config.DATA_DIR / "embeddings.pkl"
        if emb_path.exists():
            try:
                import pickle
                with emb_path.open("rb") as fh:
                    store = pickle.load(fh)
                notes = store.get("notes", {})
                before = len(notes)
                notes = {k: v for k, v in notes.items() if k not in removed}
                store["notes"] = notes
                # Atomic write
                tmp = emb_path.with_suffix(".tmp")
                with tmp.open("wb") as fh:
                    pickle.dump(store, fh)
                tmp.replace(emb_path)
                purged = before - len(notes)
            except Exception as exc:
                print(f"  [warn] could not purge embeddings: {exc}")
        print(f"  -> purged {purged} embedding entr{'y' if purged == 1 else 'ies'}.")

    # 6. Delete duplicate files
    print("\nDeleting duplicate files...")
    for p in delete_paths:
        try:
            p.unlink()
        except OSError as exc:
            print(f"  [warn] could not delete {p.name}: {exc}")
    print(f"  -> deleted {len(delete_paths) - sum(1 for p in delete_paths if p.exists())} file(s).")

    # 7. Optionally rebuild the graph
    if args.rebuild_graph:
        print("\nRebuilding graph.json...")
        import build_graph
        old_argv = sys.argv
        sys.argv = ["build_graph.py"]
        try:
            build_graph.main()
        finally:
            sys.argv = old_argv
        # Verify new counts
        from graph_component import load_graph_data
        data = load_graph_data()
        meta = data.get("meta", {})
        print(f"  -> graph.json now: {meta.get('note_count', '?')} nodes, "
              f"{meta.get('edge_count', '?')} edges")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
