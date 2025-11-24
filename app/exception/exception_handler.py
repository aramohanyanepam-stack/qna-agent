from fastapi import Request, status
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError

from main import app


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, ex: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred"},
    )

@app.exception_handler(HTTPStatusError)
async def http_exception_handler(request: Request, ex: HTTPStatusError):
    return JSONResponse(
        status_code=ex.response.status_code,
        content={"message": ex.response.text},
    )

exception_handlers = {
    Exception: generic_exception_handler,
    HTTPStatusError: http_exception_handler
}

for exception, exception_handler in exception_handlers.items():
    app.add_exception_handler(exception, exception_handler)