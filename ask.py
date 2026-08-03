#!/usr/bin/env python3
"""
ask.py — retrieve personal notes and answer questions with RAG.

Usage:
  python ask.py "What is my weekly review process?"
  python -c "from ask import ask; print(ask('How do I find my notes?'))"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Iterable

import numpy as np
import config
from lib import storage
from lib.embeddings import cosine_similarity, embed_text, load_embeddings
from lib.llm import synthesize_answer
from lib.models import AskResult, WikiNote

MAX_CONTEXT_CHARS = 1200
MAX_NOTE_BODY_CHARS = 800


def _note_text(note: WikiNote) -> str:
    return "\n".join([
        note.title or note.id,
        note.summary or "",
        note.body or "",
    ]).strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _normalize_query(query: str) -> str:
    # Remove file extensions like .png and normalize punctuation.
    query = query.lower().strip()
    query = re.sub(r"\.[a-z0-9]{1,5}$", "", query)
    return _normalize_text(query)


def _token_set(text: str) -> set[str]:
    return set(t for t in _normalize_text(text).split() if len(t) > 1)


def _extract_urls_and_emails(text: str) -> list[str]:
    text = str(text or "")
    urls = re.findall(r"(https?://[^\s\)\]\"']+|www\.[^\s\)\]\"']+)", text, flags=re.IGNORECASE)
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return urls + emails


def _build_direct_answer(query: str, note: WikiNote, values: list[str]) -> str | None:
    if not values:
        return None
    q = query.lower()
    if "linkedin" in q:
        chosen = next((v for v in values if "linkedin" in v.lower()), None)
        if chosen:
            return f"LinkedIn profile: {chosen}"
    if "gmail" in q or "email" in q or "mail" in q:
        chosen = next((v for v in values if "@" in v), None)
        if chosen:
            return f"Email address: {chosen}"
    if "url" in q or "link" in q:
        return f"Found link: {values[0]}"
    return None


def _note_search_bonus(note: WikiNote, query: str, query_terms: set[str]) -> float:
    bonus = 0.0
    query_norm = _normalize_query(query)
    note_fields = {
        "title": note.title or "",
        "slug": note.slug or "",
        "path": note.path or "",
        "summary": note.summary or "",
        "body": note.body or "",
    }

    title_norm = _normalize_text(note_fields["title"])
    path_norm = _normalize_text(note_fields["path"])
    summary_norm = _normalize_text(note_fields["summary"])
    body_norm = _normalize_text(note_fields["body"])

    if query_norm and query_norm == title_norm:
        return 2.0
    if query_norm and query_norm in title_norm:
        bonus += 1.2
    if query_norm and query_norm in path_norm:
        bonus += 1.0
    if query_norm and query_norm in summary_norm:
        bonus += 0.6
    if query_norm and query_norm in body_norm:
        bonus += 0.4

    note_terms = _token_set(" ".join(note_fields.values()))
    common = query_terms & note_terms
    if common:
        bonus += min(0.8, 0.1 * len(common))

    ql = query.lower()
    if "linkedin" in ql and "linkedin" in title_norm:
        bonus += 1.5
    if "gmail" in ql and "@gmail.com" in note.body.lower():
        bonus += 1.5
    if "email" in ql and re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", note.body):
        bonus += 1.2
    if "linkedin" in ql and "linkedin" in note.body.lower():
        bonus += 1.0

    return bonus


def _build_context(notes: list[WikiNote]) -> str:
    parts: list[str] = []
    for note in notes:
        title = note.title or note.id or note.slug
        body = (note.body or "").strip()
        snippet = body[:MAX_NOTE_BODY_CHARS]
        parts.append(
            f"Title: {title}\n"
            f"Path: {note.path}\n"
            f"PARA: {note.para}\n"
            f"Summary: {note.summary}\n"
            f"Body:\n{snippet}"
        )
    return "\n\n".join(parts)


def _load_notes_by_slug() -> dict[str, WikiNote]:
    notes = storage.read_wiki_notes()
    return {note.slug: note for note in notes}


def _load_or_build_vectors(notes_map: dict[str, WikiNote]) -> dict[str, Any]:
    embeddings = load_embeddings()
    vectors: dict[str, Any] = {}
    for slug, note in notes_map.items():
        entry = embeddings.get("notes", {}).get(slug)
        if entry is not None:
            vector = entry.get("vector")
            if isinstance(vector, np.ndarray):
                vectors[slug] = vector
                continue
            if vector is not None:
                try:
                    vectors[slug] = np.asarray(vector, dtype=np.float32)
                    continue
                except Exception:
                    pass
        vectors[slug] = embed_text(_note_text(note), embeddings.get("model"))
    return vectors


def _top_matches(question: str, notes_map: dict[str, WikiNote], vectors: dict[str, Any], top_k: int) -> list[tuple[WikiNote, float]]:
    query_vec = embed_text(question, config.EMBEDDING_MODEL)
    query_terms = _token_set(question)
    scores: list[tuple[str, float, float]] = []
    for slug, vector in vectors.items():
        try:
            emb_score = float(cosine_similarity(query_vec, vector))
        except Exception:
            emb_score = 0.0
        note = notes_map[slug]
        bonus = _note_search_bonus(note, question, query_terms)
        combined = emb_score + bonus
        scores.append((slug, combined, emb_score))

    scores.sort(key=lambda item: item[1], reverse=True)
    results: list[tuple[WikiNote, float]] = []
    for slug, combined, _ in scores[:top_k]:
        if slug in notes_map:
            results.append((notes_map[slug], combined))
    return results


def semantic_search(query: str, top_k: int = 10) -> list[dict[str, Any]]:
    """Perform a pure semantic similarity search over all wiki notes and return ranked results."""
    query = (query or "").strip()
    if not query:
        return []

    notes_map = _load_notes_by_slug()
    if not notes_map:
        return []

    vectors = _load_or_build_vectors(notes_map)
    matches = _top_matches(query, notes_map, vectors, top_k)

    results = []
    for note, score in matches:
        body_clean = re.sub(r"\s+", " ", note.body or "").strip()
        snippet = body_clean[:250] + ("..." if len(body_clean) > 250 else "")
        results.append(
            {
                "id": note.id,
                "slug": note.slug,
                "title": note.title or note.id or note.slug,
                "path": note.path,
                "para": note.para,
                "tags": note.tags,
                "summary": note.summary,
                "relevance_score": round(float(score), 4),
                "snippet": snippet,
            }
        )
    return results


def ask(question: str) -> dict[str, Any]:
    """Answer a user question from local wiki notes."""
    question = question.strip()
    if not question:
        return AskResult(answer="Please ask a non-empty question.", sources=[]).__dict__

    notes_map = _load_notes_by_slug()
    if not notes_map:
        return AskResult(
            answer="No wiki notes were found. Create notes in wiki/ and run classify.py or link.py first.",
            sources=[],
        ).__dict__

    vectors = _load_or_build_vectors(notes_map)
    top_k = config.TOP_K_RETRIEVAL
    matches = _top_matches(question, notes_map, vectors, top_k)

    sources = []
    for note, score in matches:
        sources.append(
            {
                "id": note.id,
                "slug": note.slug,
                "title": note.title or note.id,
                "path": note.path,
                "para": note.para,
                "summary": note.summary,
                "relevance_score": float(score),
            }
        )

    if matches:
        primary_note = matches[0][0]
        direct_values = _extract_urls_and_emails(primary_note.body + "\n" + primary_note.summary)
        direct_answer = _build_direct_answer(question, primary_note, direct_values)
        if direct_answer:
            return AskResult(answer=direct_answer, sources=sources).__dict__

    if not config.groq_configured():
        answer = (
            "GROQ_API_KEY is not configured. "
            "I have retrieved the most relevant notes and listed them in sources. "
            "Set GROQ_API_KEY in your environment or .env file to generate a natural-language answer."
        )
        return AskResult(answer=answer, sources=sources).__dict__

    if not sources:
        return AskResult(
            answer="I could not find any relevant notes for that query.",
            sources=[],
        ).__dict__

    if sources[0]["relevance_score"] < 0.12:
        return AskResult(
            answer=(
                "I found some notes, but none are strongly relevant to that query. "
                "Try a more specific phrase, or add a note with the exact file name or topic."
            ),
            sources=sources,
        ).__dict__

    context = _build_context([note for note, _ in matches])
    if not context.strip():
        return AskResult(
            answer="No readable note content is available to answer the question.",
            sources=sources,
        ).__dict__

    # Build the prompt from the retrieved note context.
    answer = synthesize_answer(context[:MAX_CONTEXT_CHARS], question)
    return AskResult(answer=answer.strip(), sources=sources).__dict__


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions or perform semantic search against your wiki notes.")
    parser.add_argument("question", nargs="?", help="Question or query to search")
    parser.add_argument("--search", "--semantic", action="store_true", help="Perform pure semantic search over notes")
    parser.add_argument("--pretty", action="store_true", help="Print a readable answer/search output instead of JSON")
    args = parser.parse_args()

    if not args.question:
        parser.print_help()
        sys.exit(1)

    if args.search:
        results = semantic_search(args.question)
        if args.pretty:
            print(f"Semantic Search Results for: '{args.question}'\n")
            for res in results:
                print(f"- {res['title']} ({res['path']}) [Score: {res['relevance_score']:.3f}]")
                if res['summary']:
                    print(f"  Summary: {res['summary']}")
                print()
        else:
            json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
        return

    result = ask(args.question)
    if args.pretty:
        print("Answer:\n")
        print(result["answer"])
        if result["sources"]:
            print("\nSources:")
            for source in result["sources"]:
                print(f"- {source['title']} ({source['path']}) score={source['relevance_score']:.3f}")
    else:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
