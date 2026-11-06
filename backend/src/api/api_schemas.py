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


class LegalNodeReference(BaseModel):
    """Tham chiếu gọn tới một node luật."""

    node_id: str = Field(..., description="Mã định danh node.")
    label: str = Field(..., description="Loại node (Document, Chapter, Article...).")
    number: Optional[Union[str, int]] = Field(
        default=None, description="Số hiệu (int với Article/Clause, str với cấp khác)."
    )
    title: Optional[str] = Field(default=None, description="Tiêu đề node.")
    text: Optional[str] = Field(
        default=None, description="Nội dung ngắn của Khoản/Điểm."
    )
    full_text: Optional[str] = Field(
        default=None, description="Toàn văn, chỉ có ở Article."
    )
    document_id: Optional[str] = Field(default=None, description="Văn bản chứa node.")
    parent_id: Optional[str] = Field(default=None, description="Node cha trực tiếp.")
    citation: Optional[str] = Field(
        default=None, description="Trích dẫn tuyệt đối của node."
    )


class LegalRelationship(BaseModel):
    """Một cạnh quan hệ tính từ node luật gốc."""

    relation_type: str = Field(
        ..., description="CONTAINS, REFERENCES, IMPLEMENTS, INTERPRETED_BY..."
    )
    direction: Literal["OUTGOING", "INCOMING"] = Field(
        ..., description="OUTGOING: từ node gốc đi ra; INCOMING: đi vào node gốc."
    )
    related_node: LegalNodeReference = Field(
        ..., description="Node ở đầu bên kia của quan hệ."
    )


class HybridGraphLawNode(LegalNodeReference):
    """Node luật trúng tuyển từ Hybrid Search kèm điểm và quan hệ lồng nhau."""

    score: float = Field(..., description="Điểm dùng để xếp hạng (RRF).")
    rank: int = Field(..., ge=1, description="Thứ hạng 1-indexed.")
    rrf_score: float = Field(..., description="Điểm RRF gốc.")
    semantic_rank: Optional[int] = Field(
        default=None, description="Hạng nhánh semantic."
    )
    bm25_rank: Optional[int] = Field(default=None, description="Hạng nhánh BM25.")
    retrieval_source: str = Field(
        ...,
        description="hybrid[semantic+bm25] | hybrid[semantic_only] | hybrid[bm25_only].",
    )
    relationships: list[LegalRelationship] = Field(
        default_factory=list, description="Quan hệ phân cấp và pháp lý của node."
    )


class LegalDocumentReference(BaseModel):
    """Văn bản gốc chứa các node luật liên quan."""

    node_id: str = Field(..., description="Mã định danh văn bản.")
    label: str = Field(default="Document", description="Loại node.")
    document_id: Optional[str] = Field(default=None, description="Mã văn bản.")
    title: Optional[str] = Field(default=None, description="Tên văn bản.")
    number: Optional[str] = Field(default=None, description="Số hiệu văn bản.")
    document_type: Optional[str] = Field(default=None, description="Loại văn bản.")
    effective_from: Optional[str] = Field(default=None, description="Ngày có hiệu lực.")
    effective_to: Optional[str] = Field(default=None, description="Ngày hết hiệu lực.")
    status: Optional[str] = Field(default=None, description="Trạng thái hiệu lực.")
    citation: Optional[str] = Field(
        default=None, description="Trích dẫn tuyệt đối của văn bản."
    )


class HybridGraphResult(BaseModel):
    """Payload kết quả Hybrid Search + Graph Traverse."""

    input: str = Field(..., description="Câu hỏi gốc của người dùng.")
    relevant_laws: list[HybridGraphLawNode] = Field(
        default_factory=list, description="Node luật liên quan kèm quan hệ lồng nhau."
    )
    relevant_documents: list[LegalDocumentReference] = Field(
        default_factory=list, description="Văn bản gốc chứa các node luật trên."
    )
