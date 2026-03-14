# Internal Interfaces & Contracts: OAuth
**Feature**: 003-hf-browser-login

*Note: This feature introduces a new internal module for handling OAuth logic, keeping the Streamlit UI components clean.*

## 1. OAuth Service Interface (`src/oauth.py`)

This module manages the OAuth2 flow using `requests_oauthlib`.

```python
class HFOAuthService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str): ...
    
    def get_authorization_url(self) -> tuple[str, str]:
        """
        Generates the Hugging Face authorization URL and a secure state parameter.
        Returns: (auth_url, state)
        """
        pass
        
    def fetch_token(self, authorization_response_url: str, saved_state: str) -> dict:
        """
        Exchanges the authorization code from the callback URL for an access token.
        Validates the state parameter to prevent CSRF.
        Returns the token dictionary.
        Raises an exception if the state is invalid or the exchange fails.
        """
        pass
```

## 2. Configuration Service Updates (`src/config.py`)

The config module must be updated to support writing back to the `.env` file.

```python
def save_hf_token(token: str) -> None:
    """
    Overwrites the HF_TOKEN value in the local .env file using dotenv.set_key.
    Also updates the current process environment variables.
    """
    pass

def clear_hf_token() -> None:
    """
    Removes the HF_TOKEN value from the local .env file and the current environment.
    """
    pass
```
