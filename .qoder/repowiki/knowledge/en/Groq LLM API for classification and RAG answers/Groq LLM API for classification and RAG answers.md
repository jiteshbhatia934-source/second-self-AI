---
kind: external_dependency
name: Groq LLM API for classification and RAG answers
slug: groq
category: external_dependency
category_hints:
    - vendor_identity
    - auth_protocol
scope:
    - '**'
source_files:
    - config.py
    - requirements.txt
---

### Groq
- Role: External LLM provider used by `classify.py` (PARA categorization) and `ask.py` (RAG answer synthesis).
- Integration point: `config.GROQ_API_KEY` loaded from `.env`; consumed via the `groq` Python SDK.
- Usage model: Low-temperature JSON-structured prompts for classification; moderate-low temperature for Q&A with citation requirements. Rate limits are mitigated by batching and caching results in wiki front matter.
- Deployment: On Streamlit Cloud / HF Spaces, `GROQ_API_KEY` is stored in the platform's secret manager, not in the repo.