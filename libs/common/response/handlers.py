from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from libs.common.exceptions.base import AppError

from .api_response import ApiResponse, ErrorDetail


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    response = ApiResponse.fail(
        message=exc.message,
        errors=[
            ErrorDetail(
                code=exc.code,
                message=exc.message,
            )
        ],
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(response),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    response = ApiResponse.fail(
        message="Internal server error",
        errors=[
            ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="Internal server error",
            )
        ],
    )
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(response),
    )
