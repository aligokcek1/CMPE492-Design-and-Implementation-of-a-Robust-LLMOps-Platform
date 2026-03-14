import os
from pathlib import Path

from dotenv import load_dotenv, set_key, unset_key

ENV_FILE = Path(".env")
HF_TOKEN_KEY = "HF_TOKEN"
HF_CLIENT_ID_KEY = "HF_CLIENT_ID"
HF_CLIENT_SECRET_KEY = "HF_CLIENT_SECRET"
HF_REDIRECT_URI_KEY = "HF_REDIRECT_URI"

_DEFAULT_REDIRECT_URI = "http://localhost:8501/"


def load_config():
    """Load environment variables from .env file."""
    load_dotenv(ENV_FILE)


def get_hf_token() -> str | None:
    """Return the current HF token from environment."""
    return os.getenv(HF_TOKEN_KEY)


def save_hf_token(token: str) -> None:
    """Persist HF token to .env file and update current environment."""
    ENV_FILE.touch(exist_ok=True)
    set_key(str(ENV_FILE), HF_TOKEN_KEY, token)
    os.environ[HF_TOKEN_KEY] = token


def clear_hf_token() -> None:
    """Remove HF token from .env file and current environment."""
    if ENV_FILE.exists():
        unset_key(str(ENV_FILE), HF_TOKEN_KEY)
    os.environ.pop(HF_TOKEN_KEY, None)


def get_oauth_client_id() -> str | None:
    """Return the HF OAuth application client ID."""
    return os.getenv(HF_CLIENT_ID_KEY)


def get_oauth_client_secret() -> str | None:
    """Return the HF OAuth application client secret."""
    return os.getenv(HF_CLIENT_SECRET_KEY)


def get_oauth_redirect_uri() -> str:
    """Return the OAuth redirect URI, defaulting to the Streamlit root."""
    return os.getenv(HF_REDIRECT_URI_KEY, _DEFAULT_REDIRECT_URI)
