# CMPE492-Design-and-Implementation-of-a-Robust-LLMOps-Platform Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-14

## Active Technologies
- Python 3.11+ + Streamlit, `huggingface_hub`, `python-dotenv`, `requests_oauthlib` (New) (003-hf-browser-login)
- `.env` file (HF Token storage; overwritten dynamically via `dotenv.set_key`) (003-hf-browser-login)

- Python 3.11+ + Streamlit (Frontend/App Server), `huggingface_hub` (HF API Client), `python-dotenv` (Config Management) (002-llm-hf-inference)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 003-hf-browser-login: Added Python 3.11+ + Streamlit, `huggingface_hub`, `python-dotenv`, `requests_oauthlib` (New)

- 002-llm-hf-inference: Added Python 3.11+ + Streamlit (Frontend/App Server), `huggingface_hub` (HF API Client), `python-dotenv` (Config Management)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
