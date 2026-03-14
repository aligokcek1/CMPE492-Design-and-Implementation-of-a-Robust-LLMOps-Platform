# LLM Inference App with Hugging Face Integration

A localhost-only Streamlit application for managing LLM models via Hugging Face. Connect your HF account using **OAuth2 browser login**, upload local models or reference public repositories, and trigger a mocked deployment with simulated inference.

## Prerequisites

- Python 3.11 or higher
- A [Hugging Face](https://huggingface.co) account
- A registered Hugging Face OAuth application *(see setup below)*

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## OAuth Application Registration

Before logging in, register the app as an OAuth application on Hugging Face to get your credentials.

1. Go to [Settings > Connected Apps](https://huggingface.co/settings/connected-applications) on Hugging Face.
2. Click **Create new application** and fill in:
   - **Application Name**: e.g. `Local-LLM-Inference-App`
   - **Homepage URL**: `http://localhost:8501`
   - **Callback / Redirect URI**: `http://localhost:8501/`  *(trailing slash required)*
   - **Scopes**: select `read-repos` and `write-repos` (at minimum)
3. Click **Create**. Note your **Client ID** and **App Secret**.

## Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
HF_CLIENT_ID=your_client_id_here
HF_CLIENT_SECRET=your_app_secret_here
HF_REDIRECT_URI=http://localhost:8501/
```

> The `HF_TOKEN` key is written automatically after a successful login.  
> Delete it from `.env` to force a fresh OAuth flow on next startup.

## Running the App

```bash
streamlit run src/app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

On first launch, click **Login with Hugging Face** in the **Account** page to start the OAuth flow.

## Features

| Page | What it does |
|------|-------------|
| **Account** | Connect via Hugging Face OAuth2 browser login; shows username when connected |
| **Upload Model** | Upload a local file (≤ 500 MB) to a new HF repo, or add a public repo reference |
| **Deploy & Inference** | Trigger a mocked GCP deployment and test inference with a simulated response |

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
src/
├── app.py          # Streamlit entry point & OAuth callback routing
├── config.py       # Token and OAuth credential management (.env)
├── hf_client.py    # huggingface_hub wrapper + auth-error detection
├── oauth.py        # OAuth2 authorization-code flow (HFOAuthService)
├── cache.py        # SQLite model registry
└── ui/
    ├── auth_view.py    # Account Management UI (OAuth login button)
    ├── upload_view.py  # Model Upload UI
    └── deploy_view.py  # Deploy & Inference UI

tests/
├── unit/           # Unit tests (cache, config, hf_client, oauth)
└── integration/    # Streamlit UI flow tests (auth, app callback, upload, deploy)
```
