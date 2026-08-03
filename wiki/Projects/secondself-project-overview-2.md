---
id: 'cbf3123825ef45e79c38b843811c9f19'
raw_id: '80e108ca6b544d7c8eb180549754f2b3'
para: 'Projects'
tags:
  - 'secondself'
  - 'ai'
  - 'notes'
  - 'organization'
summary: 'SecondSelf is a personal AI second brain that captures and organizes notes, links, and files. It aims to provide a comprehensive system for knowledge management and question answering.'
title: 'SecondSelf Project Overview'
created_at: '2026-07-28T06:18:24Z'
classified_at: '2026-07-29T07:25:14.071842+00:00'
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
3. Install dependencies: ```powershell
python -m pip install -r requirements.txt
```
## Configuration
`config.py` loads `.env` from the project root and exposes these values:
| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | empty | Required for classification and RAG answers. |
| `RAW_DIR` | `raw/` | Capture storage. |
| `WIKI_DIR` | `wiki/` | PARA-organized Markdown notes. |

