import sqlite3

import pytest

from src.cache import ModelCache


@pytest.fixture
def cache(tmp_path):
    db = str(tmp_path / "test.db")
    c = ModelCache(db_path=db)
    c.init_db()
    return c


# --- Phase 2: init_db ---


def test_init_db_creates_table(tmp_path):
    db = str(tmp_path / "test.db")
    c = ModelCache(db_path=db)
    c.init_db()
    conn = sqlite3.connect(db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
    assert cursor.fetchone() is not None
    conn.close()


def test_init_db_idempotent(tmp_path):
    db = str(tmp_path / "test.db")
    c = ModelCache(db_path=db)
    c.init_db()
    c.init_db()  # must not raise


# --- Phase 4: add_model, get_all_models ---


def test_add_model_and_get_all(cache):
    cache.add_model("MyModel", "LOCAL_PC", "user/inference-app-mymodel")
    models = cache.get_all_models()
    assert len(models) == 1
    assert models[0]["name"] == "MyModel"
    assert models[0]["source_type"] == "LOCAL_PC"
    assert models[0]["hf_repo_id"] == "user/inference-app-mymodel"
    assert models[0]["is_deployed"] == 0


def test_get_all_models_empty(cache):
    assert cache.get_all_models() == []


def test_add_multiple_models(cache):
    cache.add_model("Model A", "LOCAL_PC", "user/inference-app-model-a")
    cache.add_model("Model B", "PUBLIC_HF_REPO", "org/model-b")
    models = cache.get_all_models()
    assert len(models) == 2


# --- Phase 5: mark_as_deployed ---


def test_mark_as_deployed(cache):
    cache.add_model("MyModel", "LOCAL_PC", "user/inference-app-mymodel")
    cache.mark_as_deployed("user/inference-app-mymodel")
    models = cache.get_all_models()
    assert models[0]["is_deployed"] == 1
    assert models[0]["deployed_at"] is not None


def test_mark_as_deployed_nonexistent(cache):
    cache.mark_as_deployed("nonexistent/repo")  # must not raise


# --- Phase 6: sync_with_hf ---


def test_sync_with_hf_removes_orphaned_local(cache):
    cache.add_model("Gone", "LOCAL_PC", "user/inference-app-gone")
    cache.add_model("Kept", "LOCAL_PC", "user/inference-app-kept")
    cache.sync_with_hf(["user/inference-app-kept"])
    models = cache.get_all_models()
    repo_ids = [m["hf_repo_id"] for m in models]
    assert "user/inference-app-gone" not in repo_ids
    assert "user/inference-app-kept" in repo_ids


def test_sync_with_hf_keeps_public_repos(cache):
    cache.add_model("Public", "PUBLIC_HF_REPO", "org/public-model")
    cache.sync_with_hf([])  # empty HF repos, but public should be kept
    models = cache.get_all_models()
    assert len(models) == 1
