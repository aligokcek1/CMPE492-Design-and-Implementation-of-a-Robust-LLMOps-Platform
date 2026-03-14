from huggingface_hub import HfApi

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB
REPO_NAME_PREFIX = "inference-app-"


class HFAuthenticationError(Exception):
    """Raised when the HF API returns HTTP 401 or 403 (token revoked or expired)."""

    is_auth_error = True


def _extract_status_code(exc: Exception) -> int | None:
    """Extract an HTTP status code from requests.HTTPError or huggingface_hub errors."""
    response = getattr(exc, "response", None)
    if response is not None:
        return getattr(response, "status_code", None)
    return None


class HFClient:
    def __init__(self, token: str):
        self.token = token
        self._api = HfApi(token=token)
        self._whoami_cache: dict | None = None

    def _whoami(self) -> dict:
        """Call whoami() once and cache the result for the lifetime of this instance."""
        if self._whoami_cache is None:
            self._whoami_cache = self._api.whoami()
        return self._whoami_cache

    def is_valid_token(self) -> bool:
        """Returns True if the token can successfully authenticate with the HF API."""
        try:
            self._whoami()
            return True
        except Exception:
            return False

    def get_username(self) -> str:
        """Returns the HF username associated with the token."""
        return self._whoami()["name"]

    def list_user_repos(self) -> list[str]:
        """Returns a list of model repository IDs owned by the authenticated user."""
        repos = self._api.list_models(author=self.get_username())
        return [repo.id for repo in repos]

    def verify_public_repo(self, repo_id: str) -> bool:
        """Returns True if the repo_id exists and is publicly accessible."""
        try:
            self._api.repo_info(repo_id=repo_id, repo_type="model")
            return True
        except Exception:
            return False

    def call_api_or_raise(self) -> dict:
        """
        Call whoami and raise HFAuthenticationError on HTTP 401/403 (FR-008).
        Any other exception propagates normally.
        Re-runs on a fresh API call to bypass the whoami cache.
        """
        try:
            self._whoami_cache = None  # force a fresh call to detect current token state
            return self._whoami()
        except Exception as exc:
            status = _extract_status_code(exc)
            if status in (401, 403):
                raise HFAuthenticationError(str(exc)) from exc
            raise

    def upload_local_file(self, file_object, filename: str, target_repo_name: str) -> str:
        """
        Uploads a file to a new HF repository using the FR-007 naming convention:
        `inference-app-{target_repo_name}`.
        Raises ValueError if the file exceeds the 500MB limit.
        Returns the resulting hf_repo_id.
        """
        content = file_object.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise ValueError("File size exceeds the 500MB limit.")

        username = self.get_username()
        repo_name = f"{REPO_NAME_PREFIX}{target_repo_name}"
        repo_id = f"{username}/{repo_name}"

        self._api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
        self._api.upload_file(
            path_or_fileobj=content,
            path_in_repo=filename,
            repo_id=repo_id,
            repo_type="model",
        )
        return repo_id
