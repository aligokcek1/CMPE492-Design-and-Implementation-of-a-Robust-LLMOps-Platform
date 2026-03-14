import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from requests_oauthlib import OAuth2Session

# requests_oauthlib rejects plain HTTP redirect URIs by default.
# This flag allows http://localhost during local development.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

_AUTHORIZATION_BASE_URL = "https://huggingface.co/oauth/authorize"
_TOKEN_URL = "https://huggingface.co/oauth/token"
_SCOPES = ["openid", "profile", "read-repos", "write-repos", "manage-repos"]

# Temporary file used to survive the OAuth redirect (st.session_state is lost
# on a full-page navigation away from Streamlit).
_STATE_FILE = Path(".oauth_pending_state")
_STATE_TTL_SECONDS = 600  # 10 minutes


def save_pending_state(state: str) -> None:
    """Persist the OAuth state to disk before redirecting the browser to HF."""
    _STATE_FILE.write_text(json.dumps({"state": state, "ts": time.time()}))


def pop_pending_state() -> str | None:
    """
    Read and delete the pending OAuth state from disk.
    Returns None if the file is missing or the state has expired.
    """
    if not _STATE_FILE.exists():
        return None
    try:
        data = json.loads(_STATE_FILE.read_text())
        _STATE_FILE.unlink(missing_ok=True)
        if time.time() - data.get("ts", 0) > _STATE_TTL_SECONDS:
            return None
        return data.get("state")
    except Exception:
        _STATE_FILE.unlink(missing_ok=True)
        return None


class HFOAuthService:
    """Manages the Hugging Face OAuth2 authorization-code flow."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self) -> tuple[str, str]:
        """
        Generate the HF authorization URL and a cryptographically random state.
        Returns (auth_url, state). Store state in session before redirecting.
        """
        session = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            scope=_SCOPES,
        )
        auth_url, state = session.authorization_url(_AUTHORIZATION_BASE_URL)
        return auth_url, state

    def fetch_token(self, authorization_response_url: str, saved_state: str) -> dict:
        """
        Exchange the authorization code from the callback URL for an access token.
        Validates the state parameter to prevent CSRF before contacting the token endpoint.
        Raises ValueError if the state is invalid.
        Raises any requests/oauthlib exception if the token exchange fails.
        """
        parsed = urlparse(authorization_response_url)
        params = parse_qs(parsed.query)
        returned_state = params.get("state", [None])[0]

        if returned_state != saved_state:
            raise ValueError(
                "OAuth state mismatch: the 'state' parameter in the callback does not "
                "match the saved state. Possible CSRF attack — aborting token exchange."
            )

        session = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            state=saved_state,
        )
        token = session.fetch_token(
            _TOKEN_URL,
            authorization_response=authorization_response_url,
            client_secret=self.client_secret,
            include_client_id=True,
        )
        return token
