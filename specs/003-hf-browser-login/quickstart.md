# Quickstart: Hugging Face Browser Login

This guide details the additional setup required to run the application with the OAuth2 login flow.

## Prerequisites

- Existing setup from the previous feature (Python 3.11, virtual environment).
- A Hugging Face account.

## OAuth Application Registration

Before running the app locally, you must register it as an OAuth application on Hugging Face to obtain your Client ID and Client Secret.

1. Go to your Hugging Face account settings: [Settings > Connected Apps](https://huggingface.co/settings/connected-applications).
2. Click **Create new application**.
3. Fill in the details:
   - **Application Name**: (e.g., `Local-LLM-Inference-App`)
   - **Homepage URL**: `http://localhost:8501`
   - **Callback/Redirect URIs**: `http://localhost:8501/` *(Note: Streamlit runs on the root path by default, so we capture query params there)*.
   - **Scopes**: Select at least `read` and `write`.
4. Click **Create**.
5. Note your **Client ID** and **App Secret**.

## Environment Configuration

Update your `.env` file in the project root to include the new OAuth credentials. Remove any existing `HF_TOKEN` if you want to test the full flow.

```env
# OAuth App Credentials
HF_CLIENT_ID=your_client_id_here
HF_CLIENT_SECRET=your_app_secret_here
HF_REDIRECT_URI=http://localhost:8501/

# (Optional) If an HF_TOKEN is already present, the app will bypass login.
# Delete it to force the OAuth flow.
# HF_TOKEN=...
```

## Running the Application

Ensure the new dependencies are installed:
```bash
pip install requests-oauthlib
```

Start the app:
```bash
streamlit run src/app.py
```

Navigate to the "Account" section and click "Login with Hugging Face" to initiate the flow.
