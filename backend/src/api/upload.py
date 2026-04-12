import os
import posixpath
import shutil
import tempfile
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from ..api.auth_helpers import require_session
from ..models.upload import UploadStartResponse
from ..services.huggingface import upload_model_folder
from ..services.session_store import SessionError, session_store

router = APIRouter()

MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024 * 1024  # 5 GB


def _sanitise_filename(raw: str) -> str:
    """Return a safe relative path from a raw upload filename.

    Strips leading '/', rejects '..' segments, and normalises the path.
    Returns an empty string only when the input resolves to empty after
    stripping — callers should fall back to a default name.
    """
    stripped = raw.lstrip("/")
    normalised = posixpath.normpath(stripped)
    if normalised == ".":
        return ""
    parts = normalised.split("/")
    if ".." in parts:
        raise HTTPException(
            status_code=400,
            detail=f"Path traversal detected in filename: {raw}",
        )
    return normalised


@router.post("/start", response_model=UploadStartResponse)
async def start_upload(
    repository_id: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()],
    idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
    session=Depends(require_session),
) -> UploadStartResponse:
    session_id = str(uuid.uuid4())
    request_names = sorted((f.filename or "unnamed_file") for f in files)
    request_fingerprint = f"{repository_id}|{'|'.join(request_names)}"
    try:
        replay = session_store.check_idempotency(
            username=session.username,
            operation_type="upload",
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
        )
    except SessionError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    if replay is not None:
        return UploadStartResponse(**replay.response_body)

    total_size = 0
    file_contents: list[tuple[str, bytes]] = []

    for upload_file in files:
        raw_name = upload_file.filename or "unnamed_file"
        safe_rel = _sanitise_filename(raw_name)
        if not safe_rel:
            safe_rel = "unnamed_file"
        content = await upload_file.read()
        total_size += len(content)
        if total_size > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Total upload size exceeds the platform limit",
            )
        file_contents.append((safe_rel, content))

    tmp_dir = tempfile.mkdtemp(prefix="llmops_upload_")
    try:
        for safe_rel, content in file_contents:
            dest = os.path.join(tmp_dir, safe_rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(content)

        folder_results = await upload_model_folder(
            token=session.hf_token,
            local_path=tmp_dir,
            repo_id=repository_id,
        )
    except HTTPException:
        raise
    except PermissionError as exc:
        msg = str(exc)
        if "conflict" in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=403, detail=msg)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if not isinstance(folder_results, list):
        folder_results = []

    response = UploadStartResponse(session_id=session_id, folder_results=folder_results)
    session_store.store_idempotency_result(
        username=session.username,
        operation_type="upload",
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
        status_code=200,
        response_body=response.model_dump(),
    )
    return response
