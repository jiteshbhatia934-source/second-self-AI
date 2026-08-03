---
id: '5f353659f5da4b8093db2101c2aa8805'
raw_id: '80e108ca6b544d7c8eb180549754f2b3'
para: 'Projects'
tags:
  - 'secondself'
  - 'ai'
  - 'notes'
  - 'organization'
summary: 'SecondSelf is a personal AI second brain that captures, organizes, and visualizes notes. The project is currently in Phase 0 with the repository structure and configuration in place.'
title: 'SecondSelf Project Overview'
created_at: '2026-07-28T06:18:24Z'
classified_at: '2026-08-01T08:44:25.127747+00:00'
embedding_version: 'all-MiniLM-L6-v2'
---
# SecondSelf
SecondSelf is a personal AI second brain. It captures notes, links, and files; organizes them into PARA-style Markdown notes; discovers related notes with local embeddings; visualizes the resulting wiki; and answers questions from those notes.
## Project status
Phase 0 is complete: the repository structure, configuration, dependency list, and environment template are in place.
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
## Setup
1. Install Python 3.10 or later.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`.
5. Add `GROQ_API_KEY` to `.env` before using classification or question answering.
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
## Planned workflow
```text
capture → raw/ → classify → wiki/ → link → graph.json → Streamlit graph + ask
```
## Privacy
Raw captures and wiki notes can contain personal information. Keep them private by default.
