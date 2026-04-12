from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        payload = exc.detail
    else:
        payload = {"message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": payload},
    )
