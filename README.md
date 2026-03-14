# LLM Inference App with Hugging Face Integration

A localhost-only Streamlit application for managing LLM models via Hugging Face. Connect your HF account, upload local models or reference public repositories, and trigger a mocked deployment with simulated inference.

## Prerequisites

- Python 3.11 or higher
- A [Hugging Face](https://huggingface.co) account
- A HF User Access Token (with **Write** permissions if you intend to upload local models)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run src/app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

On first launch, enter your HF Access Token in the **Account** page to connect.

## Features

| Page | What it does |
|------|-------------|
| **Account** | Connect / disconnect your Hugging Face account via an access token |
| **Upload Model** | Upload a local file (≤ 500 MB) to a new HF repo, or add a public repo reference |
| **Deploy & Inference** | Trigger a mocked GCP deployment and test inference with a simulated response |

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
src/
├── app.py          # Streamlit entry point
├── config.py       # Token management (.env)
├── hf_client.py    # huggingface_hub wrapper
├── cache.py        # SQLite model registry
└── ui/
    ├── auth_view.py    # Account Management UI
    ├── upload_view.py  # Model Upload UI
    └── deploy_view.py  # Deploy & Inference UI

tests/
├── unit/           # Unit tests (cache, hf_client)
└── integration/    # Streamlit UI flow tests
```
