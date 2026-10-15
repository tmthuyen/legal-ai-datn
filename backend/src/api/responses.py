"""
responses.py
Helper dựng envelope phản hồi chuẩn cho tầng API (xem `docs/RULES.md` mục 5).

- `success`: dựng `SuccessResponse` để route trả về.
- `error_response`: dựng `JSONResponse` mang `ErrorResponse`, HTTP status = status_code.
"""

from typing import Any, Optional

from fastapi.responses import JSONResponse

from src.api.api_schemas import ErrorResponse, SuccessResponse


def success(
    result: Any,
    message: str = "Thành công",
    status_code: int = 200,
) -> SuccessResponse:
    """Dựng envelope thành công.

    Args:
        result: Dữ liệu nghiệp vụ đặt trong trường `result`.
        message: Thông báo thành công.
        status_code: Mã trạng thái (phải bằng HTTP status trả về).

    Returns:
        SuccessResponse đã dựng.
    """
    return SuccessResponse(
        status_code=status_code,
        message=message,
        result=result,
    )


def error_response(
    message: str,
    status_code: int,
    path: str,
    errors: Optional[list[str]] = None,
) -> JSONResponse:
    """Dựng JSONResponse lỗi theo envelope chuẩn.

    Args:
        message: Thông báo lỗi tổng quát.
        status_code: Mã trạng thái (HTTP status sẽ bằng giá trị này).
        path: Đường dẫn request gây lỗi.
        errors: Danh sách mô tả lỗi chi tiết.

    Returns:
        JSONResponse mang ErrorResponse với HTTP status = status_code.
    """
    payload = ErrorResponse(
        status_code=status_code,
        message=message,
        path=path,
        errors=errors or [],
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())
