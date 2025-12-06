from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom exception handler to format HTTPException responses.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"statusCode": exc.status_code, "detail": exc.detail},
    )
