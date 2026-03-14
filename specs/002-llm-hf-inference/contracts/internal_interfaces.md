# Internal Interfaces & Contracts
**Feature**: 002-llm-hf-inference

*Note: As this is a monolithic Streamlit application designed for single-user localhost deployment, there are no external-facing APIs or command-line schemas exposed to other systems. The interfaces described below represent the internal Python contracts between the UI layer and the logic/data layers to maintain a clean architecture.*

## 1. HF Client Interface (`src/hf_client.py`)

This module abstracts the `huggingface_hub` library.

```python
class HFClient:
    def __init__(self, token: str): ...
    
    def is_valid_token(self) -> bool:
        """Returns True if the initialized token can successfully ping the HF API."""
        pass
        
    def get_username(self) -> str:
        """Returns the username associated with the token."""
        pass
        
    def list_user_repos(self) -> list[str]:
        """Returns a list of repository IDs owned by the user."""
        pass
        
    def verify_public_repo(self, repo_id: str) -> bool:
        """Returns True if the repo_id exists and is publicly accessible."""
        pass
        
    def upload_local_file(self, file_object, filename: str, target_repo_name: str) -> str:
        """
        Uploads a file to a new or existing repository under the user's namespace.
        Follows the FR-007 naming convention if a new repo is created.
        Returns the resulting hf_repo_id.
        Raises an exception if the file exceeds 500MB (should be caught by UI first).
        """
        pass
```

## 2. Model Cache Interface (`src/cache.py`)

This module abstracts the SQLite database operations.

```python
class ModelCache:
    def __init__(self, db_path: str = "local_cache.db"): ...
    
    def init_db(self):
        """Creates the models table if it does not exist."""
        pass
        
    def add_model(self, name: str, source_type: str, hf_repo_id: str):
        """Adds a new model reference to the local registry."""
        pass
        
    def get_all_models(self) -> list[dict]:
        """Returns all registered models and their deployment status."""
        pass
        
    def mark_as_deployed(self, hf_repo_id: str):
        """Sets is_deployed = True for the given model."""
        pass
        
    def sync_with_hf(self, user_repos: list[str]):
        """
        Optional enhancement: Compares local cache with actual HF repos 
        and updates/removes orphaned local entries.
        """
        pass
```
