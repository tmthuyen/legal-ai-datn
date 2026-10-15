"""
retrieval.py
Route truy vấn pipeline Retrieval V1.
"""

from fastapi import APIRouter, Depends

from src.api.api_schemas import (
    ApiResponse,
    ErrorResponse,
    RetrievalRequest,
    RetrievalResult,
    SuccessResponse,
)
from src.api.dependencies import get_retrieval_service
from src.api.responses import success
from src.retrieval.retrieval_service import RetrievalService

router = APIRouter(tags=["retrieval"])


@router.post(
    "/retrieval",
    response_model=ApiResponse[RetrievalResult],
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Truy vấn Retrieval (GraphRAG)",
)
def retrieval(
    payload: RetrievalRequest,
    service: RetrievalService = Depends(get_retrieval_service),
) -> SuccessResponse[RetrievalResult]:
    """Chạy pipeline Retrieval V1 cho một câu hỏi và trả kết quả 6 key.

    Args:
        payload: Câu hỏi truy vấn của người dùng.
        service: Service Retrieval dùng chung được inject từ app state.

    Returns:
        SuccessResponse bọc `RetrievalResult` gồm input, phân cấp parse được,
        node liên quan, văn bản liên quan và quan hệ giữa các node.
    """
    result = service.retrieve(query_text=payload.query_text)
    return success(RetrievalResult(**result), message="Truy vấn thành công")
