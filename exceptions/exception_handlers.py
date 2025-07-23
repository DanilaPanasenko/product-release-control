from fastapi import Request, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.logger import logger


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {"detail": exc.detail, "status_code": exc.status_code}
        ),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(
            {"detail": "Internal server error", "status_code": 500}
        ),
    )
