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
import sys
from typing import Any

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
    scores: list[tuple[str, float]] = []
    for slug, vector in vectors.items():
        try:
            score = cosine_similarity(query_vec, vector)
        except Exception:
            score = 0.0
        scores.append((slug, float(score)))
    scores.sort(key=lambda item: item[1], reverse=True)
    return [(notes_map[slug], score) for slug, score in scores[:top_k] if slug in notes_map]


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
    parser = argparse.ArgumentParser(description="Ask questions against your wiki notes.")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--pretty", action="store_true", help="Print a readable answer instead of JSON")
    args = parser.parse_args()

    if not args.question:
        parser.print_help()
        sys.exit(1)

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
