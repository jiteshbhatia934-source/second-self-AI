# SecondSelf — Edge Cases & Corner Scenarios

Reference: [architecture.md](./architecture.md) and [implementation-plan.md](./implementation-plan.md).

Use this register while implementing each phase and during the Phase 6–7 integration and end-to-end checks. Every scenario states the expected safe behavior; add a regression test when a scenario causes a defect.

## Severity and handling

| Severity | Meaning | Expected response |
|---|---|---|
| S1 | Security, data-loss, or user-blocking issue | Fail safely, preserve data, show a clear actionable error. |
| S2 | Incorrect or degraded feature behavior | Skip the affected item where possible, log it, and continue the batch. |
| S3 | Usability, performance, or operational concern | Keep the system usable and document the limitation. |

## 1. Configuration and filesystem

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| ENV-01 | `GROQ_API_KEY` is missing, blank, invalid, or revoked. | S1 | `classify.py` and `ask()` fail with an explicit configuration or authentication message; the graph remains usable. |
| ENV-02 | `.env` is not found because a script is launched outside the repository root. | S1 | Resolve project paths from configuration/module location, or stop with the expected path in the error. |
| ENV-03 | `SIMILARITY_THRESHOLD` is negative, above 1, or non-numeric. | S2 | Reject configuration at startup rather than silently producing a dense or empty graph. |
| ENV-04 | `TOP_K_RETRIEVAL` is zero, negative, or too large. | S2 | Enforce a positive upper-bounded value and never construct an empty or oversized context unintentionally. |
| ENV-05 | Configured `RAW_DIR`, `WIKI_DIR`, or `DATA_DIR` does not exist. | S1 | Create approved writable directories where appropriate; otherwise fail with the resolved path. |
| ENV-06 | Windows/Linux separators, Unicode paths, OneDrive sync locks, or concurrent local edits occur. | S2 | Use `pathlib`, UTF-8, atomic file writes, and short retry/error reporting; never hard-code paths. |
| ENV-07 | Disk becomes full or a process is interrupted during a write. | S1 | Write to a temporary sibling file then atomically rename; do not leave a half-written JSON, Markdown, cache, or graph file. |

## 2. Capture pipeline (`capture.py`)

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| CAP-01 | Empty or whitespace-only note. | S2 | Capture remains valid with UUID and UTC timestamp; classification may label it minimally or skip with a reason. |
| CAP-02 | Very long note exceeds the LLM context window. | S2 | Preserve the complete raw capture; truncate only the classification input and log that truncation occurred. |
| CAP-03 | Note contains emoji, Hindi/RTL text, quotes, backslashes, or Markdown/YAML-looking text. | S2 | Store valid UTF-8 without corruption; shell quoting must not alter the captured content. |
| CAP-04 | User supplies a malformed URL. | S2 | Reject it clearly or save the original value as an unfetched link; never crash. |
| CAP-05 | Link fetch times out, redirects repeatedly, returns 403/404, or is non-HTML. | S2 | Store the submitted URL and capture metadata; log fetch failure without losing the capture. Limit redirects and timeouts. |
| CAP-06 | File path is missing, points to a directory, is unreadable, or is a broken symlink. | S1 | Exit non-zero before creating a raw envelope or attachment directory. |
| CAP-07 | File is zero bytes, huge, binary, scan-only PDF, or has unusual filename characters. | S2 | Preserve attachment metadata and a safe relative reference; enforce/document a size limit. Empty text extraction must not make the envelope invalid. |
| CAP-08 | Same text, URL, or file is captured twice; two captures happen concurrently. | S3 | Each capture gets a unique UUID and separate envelope. Duplicate detection is optional and must not overwrite prior raw data. |

## 3. Raw records and classification (`classify.py`)

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| RAW-01 | A raw JSON file is malformed or missing `id`, `source_type`, or required content fields. | S2 | Skip/quarantine only that capture, log its path and reason, and continue other records. |
| RAW-02 | Two raw files contain the same ID, or a raw file has been manually edited after classification. | S2 | Detect and report collision/drift; do not silently overwrite an unrelated wiki note. |
| CLS-01 | Groq rate-limits, times out, or has a temporary outage. | S1 | Use bounded exponential backoff; leave the raw record unprocessed and report a resumable batch summary. |
| CLS-02 | Model returns prose, malformed JSON, missing fields, or an invalid PARA value. | S2 | Retry once with a JSON-only reminder, validate against the four PARA categories, then quarantine/skip with a log entry. |
| CLS-03 | Raw content attempts to instruct the model to ignore system rules. | S2 | Treat source content as quoted data, never as instructions; require structured output and validate it. |
| CLS-04 | Title is blank, overly long, or includes `/`, `:`, `\\`, reserved Windows names, or emoji. | S2 | Use a safe slug and a fallback title such as `Untitled-<short-id>`; retain the human title in front matter. |
| CLS-05 | Different captures produce the same title/slug. | S2 | Append a stable short ID suffix so no wiki note is overwritten. |
| CLS-06 | YAML front matter contains colons, hashes, quotes, dates, or multiline strings. | S2 | Serialize YAML through a library; parse the result in a round-trip test. |
| CLS-07 | `--force` changes PARA category or title. | S2 | Update/move the intended note atomically, avoid duplicate notes, and preserve `raw_id`/stable note ID. |
| CLS-08 | All raw records have already been classified. | S3 | Return a successful no-op summary rather than treating it as an error. |

## 4. Embeddings and automatic links (`link.py`)

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| LNK-01 | Wiki contains zero or one note. | S3 | Generate any available embedding; create no related links and do not fail. |
| LNK-02 | A note is compared with itself, or two notes have identical content. | S2 | Exclude self-links; identical distinct notes may link once in each intended direction. |
| LNK-03 | Similarity threshold is too low (clique) or too high (no links). | S2 | Keep orphan nodes valid, record threshold in logs/config, and make tuning straightforward. |
| LNK-04 | Short/generic notes create misleading high-similarity links. | S2 | Consider a minimum-content rule and keep links reviewable in a dedicated `Related` section. |
| LNK-05 | Embedding cache is corrupted, stale, from a different model, or lacks an edited note. | S2 | Rebuild invalid entries/cache from wiki; key cache validity to body hash and embedding model version. |
| LNK-06 | Re-running `link.py` duplicates wikilinks or `Related` headings. | S2 | Make insertion idempotent; normalize and de-duplicate targets before writing. |
| LNK-07 | Corpus is large enough to exhaust memory or make all-pairs comparison slow. | S1 | Batch model encoding and matrix work; define MVP capacity and later move to ANN/FAISS if needed. |
| LNK-08 | First model download has no network access. | S1 | Show a clear model-availability error and preserve existing cache/wiki content. |

## 5. Graph export and visualization

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| GRF-01 | `wiki/` is empty. | S2 | Write valid `graph.json` with zero nodes/edges and metadata; UI explains that no notes exist. |
| GRF-02 | A Markdown file has invalid YAML/front matter. | S2 | Skip it or safely parse its body, log the path, and still export other nodes. |
| GRF-03 | Wikilink target cannot be resolved, is duplicated, or references the same note. | S2 | Log unresolved links, omit invalid/self edges, and deduplicate valid source-target edges. |
| GRF-04 | Notes form cycles or have no links. | S3 | Include cycles and orphan nodes; both are valid graph states. |
| GRF-05 | Duplicate note IDs occur in two paths. | S2 | Emit a clear conflict error or deterministic skip; never silently select an arbitrary note. |
| GRF-06 | Graph write is interrupted or graph is stale after a wiki edit. | S1 | Write atomically. The app should expose generation time and instruct the user to rebuild when stale. |
| UI-01 | `graph.json` is absent or invalid JSON. | S1 | Show a friendly in-app instruction to run `build_graph.py`; do not crash the whole Streamlit app. |
| UI-02 | Tooltip content includes HTML, JavaScript, quotes, or very long text. | S1 | Escape all note-derived text and serialize data with JSON; truncate display text safely. |
| UI-03 | Dense graph, 500+ nodes, blocked CDN, small screen, or overlapping hover targets. | S2 | Keep zoom/pan/drag usable; use local/bundled assets where deployment requires it and consider clustering/limits later. |

## 6. Retrieval and answers (`ask.py`)

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| ASK-01 | Question is blank or whitespace-only. | S2 | Validate before embedding/API use and request a question. |
| ASK-02 | Wiki/index is empty or embedding cache is missing. | S1 | Return “no knowledge base yet” or rebuild guidance; never return fabricated knowledge. |
| ASK-03 | Question is unrelated to the notes or every score is below a minimum confidence threshold. | S2 | Say the available notes are insufficient and show any sources only as low-confidence context. |
| ASK-04 | Retrieved notes conflict, are duplicated, or use a different language than the question. | S2 | State the conflict, cite sources, and avoid inventing a resolution. |
| ASK-05 | Retrieved context exceeds the provider token limit. | S2 | Bound top-k and per-note excerpts; prefer relevance-aware truncation and identify truncated context in logs. |
| ASK-06 | Prompt injection is present in a note or user asks to alter/delete data. | S1 | Treat notes as data, keep the app read-only, and answer only from approved context. |
| ASK-07 | Groq call fails mid-answer or returns unusable output. | S1 | Return a retryable error with sources/retrieval state when safe; do not claim an answer was grounded. |
| ASK-08 | Notes include passwords, API keys, or other sensitive content. | S1 | Do not expose the project publicly without sanitization; consider secret scanning/redaction before deployment. |

## 7. App, pipeline, and public deployment

| ID | Scenario | Severity | Expected behavior / test |
|---|---|---:|---|
| APP-01 | App has no API key in Streamlit secrets. | S1 | Graph tab works; Ask tab is disabled or gives setup instructions. |
| APP-02 | User submits multiple asks, refreshes during an ask, or opens multiple tabs. | S2 | Avoid shared mutable request state; cache the embedding model safely and tolerate repeated read-only requests. |
| APP-03 | A public UI exposes capture, upload, arbitrary file paths, or pipeline subprocess buttons. | S1 | Keep these actions local-only or strongly authenticated; public deployment must not enable arbitrary execution. |
| PL-01 | Scripts run out of order (`link` before `classify`, graph before links) or pipeline stops mid-run. | S2 | Each stage validates prerequisites, does not corrupt outputs, and reports what remains to run. |
| PL-02 | New capture exists but classify/link/graph have not been refreshed. | S2 | Make stale state visible in command/app guidance; do not imply the graph or answers include the new capture. |
| DEP-01 | Public repo accidentally includes raw/private wiki data or `.env`. | S1 | Use a sanitized demo dataset, verify `.gitignore`, rotate exposed keys immediately, and review files before push. |
| DEP-02 | Cold start/model download, incompatible Python/dependency versions, or oversized Torch build breaks deployment. | S1 | Pin dependencies, use supported Python, test a clean deploy, and document first-load behavior. |
| DEP-03 | Committed `graph.json` does not match committed demo wiki. | S2 | Rebuild and validate graph as part of release/deploy checks. |
| DEP-04 | Public ask endpoint is abused and consumes provider quota. | S2 | Rate-limit where available, use restricted demo credentials, and monitor failures/usage. |

## 8. Regression smoke checklist

Run these after Phase 5 and before Phase 8 deployment:

- [ ] Capture an empty note, Unicode note, unreachable link, missing file, and zero-byte file (`CAP-01`–`CAP-07`).
- [ ] Classify a corrupt raw record, invalid model response, duplicate title, and an already-processed batch (`RAW-01`, `CLS-02`, `CLS-05`, `CLS-08`).
- [ ] Link one note, duplicate bodies, edited notes, and a rebuilt/corrupt embedding cache (`LNK-01`, `LNK-02`, `LNK-05`, `LNK-06`).
- [ ] Build a graph with orphan nodes, an unresolved wikilink, duplicate links, and untrusted tooltip text (`GRF-03`, `UI-02`).
- [ ] Ask with a blank question, empty index, off-topic question, conflicting notes, and forced API failure (`ASK-01`–`ASK-07`).
- [ ] Start the app without `graph.json` and without an API key (`UI-01`, `APP-01`).
- [ ] Perform one full capture → classify → link → graph → ask run and verify sources point to real wiki notes (`PL-02`).
- [ ] Review public deployment contents for private notes and secrets (`DEP-01`).

## Maintenance

Add a row before implementing any new ingestion route, auth capability, PDF extraction, scheduled workflow, or sharing feature. Where practical, name tests after their IDs (for example, `test_duplicate_slug_cls_05`) so this document remains connected to regression coverage.
