# Research & Technical Decisions: Robust Model Upload

## Language/Version
- **Decision**: Python 3.11 for Backend; TypeScript with React (Vite) for Frontend.
- **Rationale**: Python is the industry standard for AI/ML tooling and integrates natively with Hugging Face libraries. TypeScript/React provides a robust, strongly-typed frontend for complex file upload interfaces.
- **Alternatives considered**: Node.js backend (rejected due to weaker AI ecosystem), vanilla JS frontend (rejected due to lack of type safety for complex state management).

## Primary Dependencies
- **Decision**: `FastAPI` (Backend), `huggingface_hub` (Backend), `axios` (Frontend).
- **Rationale**: `FastAPI` offers high performance and automatic OpenAPI docs. `huggingface_hub` Python library has built-in robust upload methods (e.g., `upload_folder`) with resume capabilities, perfectly matching our 10GB robust upload constraint. `axios` allows fine-grained control over upload progress events.
- **Alternatives considered**: Direct REST API calls to Hugging Face (rejected because `huggingface_hub` handles chunking, concurrency, and retries natively).

## Testing
- **Decision**: `pytest` and `pytest-asyncio` for Backend; `vitest` and `React Testing Library` for Frontend.
- **Rationale**: Strict TDD mandates fast, reliable test runners. `pytest` is the Python standard. `vitest` offers extremely fast execution for React components compared to Jest, aiding the Red-Green-Refactor cycle.
- **Alternatives considered**: `unittest` (too verbose), `Jest` (slower than `vitest`).