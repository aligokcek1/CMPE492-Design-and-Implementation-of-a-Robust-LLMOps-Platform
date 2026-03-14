# Phase 0: Research & Technical Decisions

**Feature**: LLM Inference App with Hugging Face Integration
**Date**: 2026-03-14

## Technical Context & Decisions

### 1. Frontend Framework
- **Decision**: Streamlit (Python)
- **Rationale**: The user explicitly requested to keep the frontend as basic as possible, prioritizing functionality. Streamlit allows building a functional, interactive UI entirely in Python without needing a separate frontend stack (React/Vue/HTML). It's highly suited for ML/LLM prototyping and easily handles forms (HF Token input), file uploads (Model upload), and basic text display (Mocked inference).
- **Alternatives considered**: React + FastAPI (too complex for a basic frontend requirement), Gradio (similar to Streamlit, but Streamlit offers slightly better out-of-the-box state management for multi-step flows like auth -> upload -> deploy).

### 2. Backend & API
- **Decision**: Streamlit (Integrated Backend) + `huggingface_hub` Python library.
- **Rationale**: Since the app is a single-user, localhost-only tool (per FR-010, FR-013), splitting into a separate frontend and backend is an unnecessary abstraction (violating Constitution Principle III: Clean & Concise Implementation). Streamlit can directly execute the Python logic to interact with the Hugging Face API using their official `huggingface_hub` client.
- **Alternatives considered**: FastAPI backend + Streamlit frontend (unnecessary complexity for a single-user local tool).

### 3. Storage (Local Cache & Config)
- **Decision**: `python-dotenv` for token storage; SQLite (via Python's built-in `sqlite3`) for the local model registry cache.
- **Rationale**: 
  - Token (FR-010): Storing the HF Token in a local `.env` file accessed via `python-dotenv` is secure for a local-only app and standard practice.
  - Cache (FR-012): SQLite is zero-setup, built into Python, and perfectly sufficient for caching metadata (ID, source, sync status) to improve UI responsiveness without requiring an external database server.
- **Alternatives considered**: JSON file for cache (prone to corruption with concurrent reads/writes if UI refreshes quickly), PostgreSQL (overkill).

### 4. Direct Browser Uploads to HF (FR-004)
- **Decision**: Use `huggingface_hub`'s `upload_file` or `HfApi().upload_file` within Streamlit.
- **Rationale**: While the spec originally noted "direct from client browser to HF API", in a Streamlit context, the "client" and "server" run tightly coupled on localhost. Streamlit's `st.file_uploader` streams the file to the local Python process, which then immediately streams it to HF via the `huggingface_hub` library. Given it's a localhost app, this satisfies the intent of not routing through an external remote backend, keeping the architecture simple. If a true direct-to-S3/GCS browser upload was strictly required, it would mandate a complex custom React component inside Streamlit, which conflicts with "keep frontend basic".

### 5. Testing Framework
- **Decision**: `pytest`
- **Rationale**: Industry standard for Python. Supports unit testing the HF integration logic (mocking the `huggingface_hub` API) and integrating with Streamlit's testing framework (`streamlit.testing.v1`). Aligns with Constitution Principle II (Mandatory TDD).
