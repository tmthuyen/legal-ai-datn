"""
dependencies.py
Các dependency lấy service dùng chung từ `app.state` cho các route.

Service được khởi tạo một lần trong `lifespan` của server và lưu ở `app.state.services`;
các route chỉ đọc lại, không tự khởi tạo.
"""

from fastapi import Request

from src.common.container import AppServices
from src.retrieval.retrieval_service import RetrievalService


def get_services(request: Request) -> AppServices:
    """Lấy tập service dùng chung từ app state.

    Args:
        request: Request hiện tại của FastAPI.

    Returns:
        AppServices đã được nạp khi server khởi động.
    """
    return request.app.state.services


def get_retrieval_service(request: Request) -> RetrievalService:
    """Lấy service Retrieval dùng chung từ app state.

    Args:
        request: Request hiện tại của FastAPI.

    Returns:
        RetrievalService dùng chung cho mọi request.
    """
    return get_services(request).retrieval_service
