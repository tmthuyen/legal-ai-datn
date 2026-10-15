"""
api_schemas.py
Định nghĩa envelope phản hồi chuẩn và các payload cho tầng API.

Quy ước (xem `docs/RULES.md` mục 5):
- Thành công: `SuccessResponse[T]` = {success, status_code, message, result}.
- Thất bại:   `ErrorResponse`      = {success, status_code, message, path, errors}.
- HTTP status code luôn bằng `status_code` trong body.
"""

from typing import Any, Generic, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Envelope cho response thành công."""

    success: Literal[True] = True
    status_code: int = 200
    message: str = "Thành công"
    result: T


class ErrorResponse(BaseModel):
    """Envelope cho response thất bại."""

    success: Literal[False] = False
    status_code: int = 500
    message: str = "Lỗi hệ thống"
    path: str = ""
    errors: list[str] = Field(default_factory=list)


class ApiResponse:
    """Alias generic cho `response_model`: `ApiResponse[T]` → envelope thành công/lỗi.

    Không khởi tạo trực tiếp; chỉ dùng trong khai báo route, ví dụ
    `response_model=ApiResponse[RetrievalResult]`. Việc này giữ đúng cú pháp
    `ApiResponse[T]` dù pydantic xoá `TypeVar` khi ghép Union.
    """

    def __class_getitem__(cls, item: Any) -> Any:
        """Trả về Union envelope thành công (theo `item`) hoặc envelope lỗi."""
        return Union[SuccessResponse[item], ErrorResponse]


class RetrievalRequest(BaseModel):
    """Body request cho endpoint retrieval."""

    query_text: str = Field(
        ...,
        min_length=1,
        description="Câu hỏi người dùng (có trích dẫn vị trí luật).",
    )


class HealthData(BaseModel):
    """Payload trạng thái sẵn sàng của dịch vụ."""

    status: str = Field(..., description="Trạng thái tổng quát của dịch vụ.")
    app_name: str = Field(..., description="Tên ứng dụng.")
    app_version: str = Field(..., description="Phiên bản ứng dụng.")
    services_ready: bool = Field(
        ..., description="Service dùng chung đã được nạp vào app state chưa."
    )
    neo4j_connected: bool = Field(..., description="Kết nối Neo4j có khả dụng không.")


class RetrievalResult(BaseModel):
    """Payload kết quả pipeline Retrieval V1 (6 key đặc tả)."""

    input: str = Field(..., description="Câu hỏi gốc của người dùng.")
    extracted_hierarchy: Optional[dict[str, Any]] = Field(
        default=None, description="Phân cấp luật parse được từ câu hỏi."
    )
    node_information: Optional[dict[str, Any]] = Field(
        default=None, description="Thông tin node đích parse được từ câu hỏi."
    )
    related_documents: list[dict[str, Any]] = Field(
        default_factory=list, description="Danh sách văn bản liên quan."
    )
    related_nodes: list[dict[str, Any]] = Field(
        default_factory=list, description="Danh sách node liên quan."
    )
    relationships: list[dict[str, Any]] = Field(
        default_factory=list, description="Danh sách quan hệ giữa các node liên quan."
    )
