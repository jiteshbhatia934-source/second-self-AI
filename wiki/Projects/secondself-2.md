---
id: 'secondself-2'
raw_id: 'secondself-2'
para: 'Projects'
tags:
  - 'notes'
  - 'graph'
  - 'wiki'
  - 'capture'
  - 'configuration'
summary: '# SecondSelf  SecondSelf is a personal AI second brain.'
title: 'SecondSelf'
created_at: '2026-08-01T02:31:09.812541+00:00'
classified_at: '2026-08-01T02:31:09.812541+00:00'
embedding_version: 'all-MiniLM-L6-v2'
---
# SecondSelf

SecondSelf is a personal AI second brain. It captures notes, links, and files; organizes them into PARA-style Markdown notes; discovers related notes with local embeddings; visualizes the resulting wiki; and answers questions from those notes.

## Project status

Phase 0 is complete: the repository structure, configuration, dependency list, and environment template are in place. The capture, classification, linking, graph, and RAG modules will be added in later phases.

## Repository layout

```text
raw/                 Immutable captures and file attachments
wiki/                Organized Markdown notes, split by PARA category
  Projects/
  Areas/
  Resources/
  Archives/
data/                Regenerable embedding cache and index data
docs/                Architecture, implementation plan, and edge-case register
config.py            Shared paths and environment configuration
```

See [the architecture](docs/architecture.md), [the implementation plan](docs/implementation-plan.md), and [the edge-case register](docs/edge-case.md).

## Setup

1. Install Python 3.10 or later.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`.
5. Add `GROQ_API_KEY` to `.env` before using classification or question answering.

The key is not needed for the local folder structure or future capture command. `.env` is intentionally ignored by Git.

## Configuration

`config.py` loads `.env` from the project root and exposes these values:

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | empty | Required for classification and RAG answers. |
| `RAW_DIR` | `raw/` | Capture storage. |
| `WIKI_DIR` | `wiki/` | PARA-organized Markdown notes. |
| `DATA_DIR` | `data/` | Embedding cache and indexes. |
| `GRAPH_PATH` | `graph.json` | Generated graph export. |
| `SIMILARITY_THRESHOLD` | `0.80` | Minimum similarity used for auto-links. |
| `TOP_K_RETRIEVAL` | `8` | Number of notes used for an answer. |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model. |

Relative path overrides are resolved from this repository, not from the shell's current folder. Configuration rejects invalid similarity and retrieval values at startup.

## Planned workflow

```text
capture → raw/ → classify → wiki/ → link → graph.json → Streamlit graph + ask
```

The implementation plan lists the commands as each stage is introduced.

## Privacy

Raw captures and wiki notes can contain personal information. Keep them private by default. Before any public deployment, use a sanitized demo dataset and never commit `.env` or API keys.


## Related

- [[secondself-1]]
- [[secondself]]

