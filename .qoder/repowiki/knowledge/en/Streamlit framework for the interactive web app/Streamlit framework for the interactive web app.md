---
kind: external_dependency
name: Streamlit framework for the interactive web app
slug: streamlit
category: external_dependency
category_hints:
    - vendor_identity
    - framework_behavior
scope:
    - '**'
source_files:
    - requirements.txt
    - README.md
---

### Streamlit
- Integration point: Entry point `streamlit run app.py`; secrets (`GROQ_API_KEY`) injected via `st.secrets` on hosted platforms.
- Usage model: Two tabs — "Brain" (graph visualization) and "Ask" (text input + markdown answer with source expanders). Graph data loaded from `graph.json` at startup.
- Deployment target: Streamlit Community Cloud or Hugging Face Spaces, with public URL as final deliverable.