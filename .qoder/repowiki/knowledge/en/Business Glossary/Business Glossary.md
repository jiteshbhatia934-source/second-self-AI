---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### SecondSelf
- Definition：The project's product name for a personal AI second brain that captures notes, links, and files; organizes them into PARA-style Markdown; discovers related notes via local embeddings; visualizes relationships as an interactive graph; and answers questions grounded in those notes.
- Aliases：secondself、second self

### PARA
- Definition：The folder taxonomy used to organize wiki notes: Projects, Areas, Resources, Archives. Each note is placed under exactly one PARA subfolder and tagged accordingly.
- Aliases：para folders、para categories

### raw/
- Definition：Append-only capture storage directory where each ingestion (note, link, file) is written as an immutable JSON envelope with a UUID id and ISO-8601 timestamp before any processing.
- Aliases：raw captures、raw directory

### wiki/
- Definition：Curated Markdown notes organized under PARA subfolders, using YAML front matter for metadata (id, raw_id, para, tags, summary, title, timestamps) and wikilinks [[id]] for cross-references.
- Aliases：wiki directory、wiki notes

### graph.json
- Definition：Exported graph artifact containing a meta block (generated_at, note_count, edge_count), a nodes array (id, label, para, tags, summary, path), and an edges array (source, target, type: wikilink|similarity). Consumed by the interactive graph UI and the Streamlit app.
- Aliases：graph export、graph data

### embeddings.pkl
- Definition：Persisted pickle index mapping note ids to float vectors produced by the sentence-transformers model, enabling cosine-similarity lookup without recomputing embeddings on every run.
- Aliases：embedding cache、vector index

### wikilink
- Definition：A cross-reference syntax [[target-id-or-slug]] embedded in wiki note bodies that build_graph.py parses to derive edges in the graph; targets are resolved by note id, slug, or filename.
- Aliases：[[wikilink]]、wiki link

### similarity edge
- Definition：An optional edge type in graph.json representing auto-discovered connections between notes whose embedding cosine similarity exceeds SIMILARITY_THRESHOLD, distinct from explicit wikilink edges.
- Aliases：auto-link、embedding link

### RAG
- Definition：Retrieval-Augmented Generation: the ask() function embeds a question, retrieves top-k most similar wiki notes by cosine similarity, builds a context from their titles/summaries/bodies, and asks Groq to synthesize an answer citing sources.
- Aliases：rag、retrieval augmented generation

### capture
- Definition：The Phase 1 pipeline step implemented by capture.py that ingests a note text, URL, or file into raw/ as an immutable JSON envelope with a unique id and UTC timestamp.
- Aliases：capture pipeline、the archivist

### classify
- Definition：The Phase 2.1 step implemented by classify.py that calls Groq/Llama 3 to assign each raw capture a PARA category, tags, summary, and human-readable title, then writes it as a wiki note.
- Aliases：classification、sorting hat

### link
- Definition：The Phase 2.2 step implemented by link.py that computes embeddings for all wiki notes and auto-inserts [[wikilink]] references when similarity exceeds the configured threshold.
- Aliases：auto-link、connect the dots

### build_graph
- Definition：The Phase 3.1 step implemented by build_graph.py that walks wiki notes, extracts front matter and wikilinks, resolves targets, and exports graph.json conforming to architecture section 4.3.
- Aliases：graph builder、the cartographer

### ask
- Definition：The Phase 4.1 RAG function implemented by ask.py that returns answer and sources by retrieving top-k notes and prompting Groq to answer only from the provided context.
- Aliases：ask function、the oracle

### pipeline
- Definition：Optional orchestration script (pipeline.py) that runs classify, link, build_graph in sequence for a full refresh after new captures.
- Aliases：full pipeline、refresh pipeline

### Phase 0–9
- Definition：The phased implementation plan dividing SecondSelf into sequential milestones: 0=setup, 1=capture, 2=classify, 3=link, 4=graph+UI, 5=RAG+app, 6=integration tests, 7=E2E sign-off, 8=deploy, 9=production verification.
- Aliases：phases、implementation phases、weekly milestones
