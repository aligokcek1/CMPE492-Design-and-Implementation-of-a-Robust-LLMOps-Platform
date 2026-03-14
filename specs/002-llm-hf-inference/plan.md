# Implementation Plan: LLM Inference App with Hugging Face Integration

**Branch**: `002-llm-hf-inference` | **Date**: 2026-03-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-llm-hf-inference/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a localhost-only LLM inference app that integrates with Hugging Face for model management. Users connect their HF account via an access token, upload models (local files up to 500MB or public repo references), and trigger a mocked deployment to GCP. The app features a basic UI with mocked inference capabilities.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Streamlit (Frontend/App Server), `huggingface_hub` (HF API Client), `python-dotenv` (Config Management)
**Storage**: SQLite (Local cache for model registry, `sqlite3`), `.env` file (HF Token storage)
**Testing**: `pytest`, `streamlit.testing.v1`, `unittest.mock`
**Target Platform**: Localhost / Local PC
**Project Type**: Streamlit Web Application
**Performance Goals**: UI loads instantly; syncs HF metadata in < 2s. Local model uploads (under 100MB) complete within 2 minutes.
**Constraints**: 500MB hard limit on local file uploads. Single-user mode only. Mocked deployment and inference.
**Scale/Scope**: Single local user, managing personal HF repositories and a mocked deployment pipeline.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Security-First Cloud Readiness**: PASS. HF Token is stored securely in a local `.env` file, never committed or exposed in the browser. App is local-only, adhering to constraints.
- **II. Mandatory Test-Driven Development (TDD)**: PASS. `pytest` selected. The plan dictates writing tests (unit for HF logic, Streamlit integration tests for UI) before implementation.
- **III. Clean & Concise Implementation**: PASS. Using Streamlit to combine frontend and backend avoids unnecessary wrappers and complex multi-repo architectures. Direct use of `huggingface_hub` avoids reinventing API calls.
- **IV. Scalable Architecture & Observability**: PASS. While a local tool, the hybrid cache design (SQLite + HF API sync) ensures the app scales locally without API rate-limiting issues on every render.
- **V. Practical & Iterative Delivery**: PASS. Streamlit allows rapid, iterative delivery of the functional MVP requested by the user.

## Project Structure

### Documentation (this feature)

```text
specs/002-llm-hf-inference/
├── plan.md              # This file
├── research.md          # Technical decisions
├── data-model.md        # Entities and cache schema
├── quickstart.md        # Setup instructions
└── tasks.md             # Implementation tasks (generated later)
```

### Source Code (repository root)

```text
src/
├── app.py                 # Streamlit entry point
├── config.py              # Environment and token management
├── hf_client.py           # Wrapper around huggingface_hub
├── cache.py               # SQLite database operations
└── ui/                    # Streamlit components
    ├── auth_view.py       # Login/Disconnect UI
    ├── upload_view.py     # Model source selection and upload UI
    └── deploy_view.py     # Mocked deployment and inference UI

tests/
├── integration/           # Streamlit UI flow tests
└── unit/                  # Unit tests for hf_client, cache, config
```

**Structure Decision**: A single Python package structure using Streamlit. The UI components are separated into a `ui/` directory for readability, while core logic (auth, HF API, caching) remains in the root `src/` directory to promote clean separation of concerns within the monolithic app.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(No violations. The architecture is as simple as possible for the requirements.)*
