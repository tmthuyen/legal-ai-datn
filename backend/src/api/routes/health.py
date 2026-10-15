"""
health.py
Route kiểm tra trạng thái dịch vụ.
"""

from fastapi import APIRouter, Request

from src.api.api_schemas import (
    ApiResponse,
    ErrorResponse,
    HealthData,
    SuccessResponse,
)
from src.api.responses import success
from src.common.setting_config import get_settings

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    responses={500: {"model": ErrorResponse}},
    summary="Kiểm tra trạng thái dịch vụ",
)
def health(request: Request) -> SuccessResponse[HealthData]:
    """Trả về trạng thái app, service dùng chung và kết nối Neo4j.

    Args:
        request: Request hiện tại của FastAPI (dùng để truy cập app state).

    Returns:
        SuccessResponse bọc `HealthData` mô tả mức độ sẵn sàng của dịch vụ.
    """
    settings = get_settings()
    services = getattr(request.app.state, "services", None)

    neo4j_connected = False
    if services is not None:
        neo4j_connected = services.neo4j_client.verify_connectivity()

    data = HealthData(
        status="ok" if services is not None else "starting",
        app_name=settings.app_name,
        app_version=settings.app_version,
        services_ready=services is not None,
        neo4j_connected=neo4j_connected,
    )
    return success(data, message="Hệ thống hoạt động bình thường")
