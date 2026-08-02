---
kind: external_dependency
name: Local embedding model engine (all-MiniLM-L6-v2)
slug: sentence-transformers
category: external_dependency
category_hints:
    - framework_behavior
    - client_constraint
scope:
    - '**'
source_files:
    - config.py
    - requirements.txt
---

### sentence-transformers
- Role: Local embedding engine producing note vectors for similarity-based auto-linking and retrieval-augmented question answering.
- Integration point: Model name controlled by `EMBEDDING_MODEL` env var (default `all-MiniLM-L6-v2`); vectors persisted to `data/embeddings.pkl` keyed by note id.
- Usage model: Batch encoding of all wiki notes; cosine similarity computed with numpy. Embedding cache is invalidated when a note's content hash changes.
- Constraint: First run downloads the model weights — this causes a cold start on both local dev and cloud deployments; the README documents this delay.