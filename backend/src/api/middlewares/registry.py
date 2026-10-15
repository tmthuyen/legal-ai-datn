"""
registry.py
Nơi tập trung đăng ký toàn bộ middleware cho FastAPI app.

Muốn thêm middleware mới: thêm một lời gọi `app.add_middleware(...)` trong
`register_middlewares`. Lưu ý thứ tự stack của Starlette: middleware thêm
**sau cùng** nằm **ngoài cùng** (chạy trước, kết thúc sau).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middlewares.request_logging import RequestLoggingMiddleware
from src.common.setting_config import Settings


def register_middlewares(app: FastAPI, settings: Settings) -> None:
    """Đăng ký toàn bộ middleware dùng chung cho mọi request.

    Args:
        app: FastAPI app cần gắn middleware.
        settings: Cấu hình ứng dụng (nguồn cấu hình CORS...).
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
