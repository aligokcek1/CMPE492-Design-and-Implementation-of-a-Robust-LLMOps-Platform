import os
from pathlib import Path

from dotenv import load_dotenv, set_key, unset_key

ENV_FILE = Path(".env")
HF_TOKEN_KEY = "HF_TOKEN"


def load_config():
    """Load environment variables from .env file."""
    load_dotenv(ENV_FILE)


def get_hf_token() -> str | None:
    """Return the current HF token from environment."""
    return os.getenv(HF_TOKEN_KEY)


def save_hf_token(token: str):
    """Persist HF token to .env file and update current environment."""
    ENV_FILE.touch(exist_ok=True)
    set_key(str(ENV_FILE), HF_TOKEN_KEY, token)
    os.environ[HF_TOKEN_KEY] = token


def clear_hf_token():
    """Remove HF token from .env file and current environment."""
    if ENV_FILE.exists():
        unset_key(str(ENV_FILE), HF_TOKEN_KEY)
    os.environ.pop(HF_TOKEN_KEY, None)
