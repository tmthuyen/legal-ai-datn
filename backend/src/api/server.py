"""
server.py
Điểm khởi tạo FastAPI app cho Legal AI.

Nhiệm vụ:
- Nạp model và khởi tạo toàn bộ service dùng chung **một lần** khi server start.
- Lưu service vào `app.state.services` để mọi request tái sử dụng.
- Đăng ký 2 API: `GET /health` và `POST {api_prefix}/retrieval`.
"""

import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.middlewares.registry import register_middlewares
from src.api.responses import error_response
from src.api.routes import health, retrieval
from src.common.container import build_services
from src.common.custom_exception import CustomException
from src.common.setting_config import Settings, get_settings
from src.utils.logger import setup_logger

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = setup_logger("api_server", "api_server.log")

# Phân loại exception Python "thường" (ngoài CustomException):
# - auth       : lỗi xác thực/quyền
# - validation : lỗi dữ liệu đầu vào
# - còn lại    : 500 (lỗi hệ thống)
CLASSIFIED_EXCEPTIONS: dict[type[Exception], tuple[int, str]] = {
    PermissionError: (403, "Không có quyền truy cập"),
    ValueError: (400, "Dữ liệu đầu vào không hợp lệ"),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Nạp model + service dùng chung khi start và giải phóng khi shutdown.

    Args:
        app: FastAPI app đang chạy.
    """
    settings: Settings = get_settings()

    logger.info("Khởi động server: nạp model và khởi tạo service dùng chung...")
    app.state.services = build_services(settings)
    logger.info("Nạp model và service dùng chung hoàn tất. Server sẵn sàng.")

    try:
        yield
    finally:
        logger.info("Tắt server: giải phóng tài nguyên...")
        services = getattr(app.state, "services", None)
        if services is not None:
            services.close()


async def custom_exception_handler(
    request: Request, exc: CustomException
) -> JSONResponse:
    """Trả lỗi nghiệp vụ theo `status_code` khai báo trong `CustomException`.

    Args:
        request: Request hiện tại.
        exc: CustomException được raise từ tầng nghiệp vụ.

    Returns:
        JSONResponse mang ErrorResponse với HTTP status = exc.status_code.
    """
    logger.warning(
        "CustomException [%s] tại %s: %s",
        exc.status_code,
        request.url.path,
        exc.message,
    )
    return error_response(
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        errors=[exc.message],
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Trả lỗi 422 khi body/query không hợp lệ với schema.

    Args:
        request: Request hiện tại.
        exc: Lỗi validate của FastAPI/pydantic.

    Returns:
        JSONResponse mang ErrorResponse với HTTP status 422.
    """
    errors = [
        f"{'.'.join(str(loc) for loc in err.get('loc', []))}: {err.get('msg', '')}"
        for err in exc.errors()
    ]
    logger.warning("RequestValidationError tại %s: %s", request.url.path, errors)
    return error_response(
        message="Dữ liệu đầu vào không hợp lệ",
        status_code=422,
        path=request.url.path,
        errors=errors,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Trả lỗi theo `status_code` của HTTPException (401/403/404/405...).

    Args:
        request: Request hiện tại.
        exc: HTTPException do Starlette/FastAPI raise.

    Returns:
        JSONResponse mang ErrorResponse với HTTP status = exc.status_code.
    """
    logger.warning(
        "HTTPException [%s] tại %s: %s", exc.status_code, request.url.path, exc.detail
    )
    return error_response(
        message=str(exc.detail),
        status_code=exc.status_code,
        path=request.url.path,
        errors=[str(exc.detail)],
    )


def make_classified_exception_handler(status_code: int, message: str) -> Any:
    """Tạo handler cho một loại exception đã phân loại (auth/validation).

    Args:
        status_code: Mã trạng thái áp cho loại exception này.
        message: Thông báo lỗi trả cho client.

    Returns:
        Hàm handler bất đồng bộ dùng cho `app.add_exception_handler`.
    """

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        """Trả lỗi đã phân loại cho exception tương ứng."""
        logger.warning(
            "%s [%s] tại %s: %s", type(exc).__name__, status_code, request.url.path, exc
        )
        return error_response(
            message=message,
            status_code=status_code,
            path=request.url.path,
            errors=[str(exc)],
        )

    return handler


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Trả lỗi 500 cho mọi exception không lường trước và log đầy đủ traceback.

    Args:
        request: Request hiện tại.
        exc: Exception không nằm trong danh sách phân loại.

    Returns:
        JSONResponse mang ErrorResponse với HTTP status 500 (không lộ nội bộ).
    """
    logger.error("Unhandled exception tại %s: %s", request.url.path, exc, exc_info=exc)
    return error_response(
        message="Lỗi hệ thống",
        status_code=500,
        path=request.url.path,
        errors=[],
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký toàn bộ exception handler tập trung cho app.

    Phân loại: `CustomException` theo status_code; auth/validation theo
    `CLASSIFIED_EXCEPTIONS`; các exception khác trả 500.

    Args:
        app: FastAPI app cần đăng ký handler.
    """
    app.add_exception_handler(CustomException, custom_exception_handler)
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    for exc_type, (status_code, message) in CLASSIFIED_EXCEPTIONS.items():
        app.add_exception_handler(
            exc_type, make_classified_exception_handler(status_code, message)
        )

    app.add_exception_handler(Exception, unhandled_exception_handler)


def create_app() -> FastAPI:
    """Tạo và cấu hình FastAPI app.

    Returns:
        FastAPI app đã gắn lifespan, middleware, exception handler và các route.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    register_middlewares(app, settings)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(retrieval.router, prefix=settings.api_prefix)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=settings.app_port,
    )
