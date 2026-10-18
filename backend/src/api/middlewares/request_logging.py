"""
request_logging.py
Middleware ghi log thông tin và thời gian xử lý của mọi request.

Mỗi request được log một dòng gồm: method + url, tên request (route), status code,
response time (ms), IP client và user-agent.
"""

import time
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logger import setup_logger

logger = setup_logger("request_logging", "request_logging.log")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log mọi request: response time, tên request, IP, user-agent, url."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Đo thời gian và ghi log sau khi request xử lý xong.

        Args:
            request: Request đang đi qua middleware.
            call_next: Hàm gọi tầng xử lý phía trong (router + exception handler).

        Returns:
            Response trả về cho client (giữ nguyên, không đổi nội dung).

        Raises:
            Exception: Re-raise mọi lỗi sau khi đã ghi log để tầng ngoài xử lý.
        """
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            self._log(request, 500, duration_ms, error=exc)
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        self._log(request, response.status_code, duration_ms)
        return response

    def _log(
        self,
        request: Request,
        status_code: int,
        duration_ms: float,
        error: Optional[BaseException] = None,
    ) -> None:
        """Ghi một dòng log cho request.

        Args:
            request: Request cần log.
            status_code: HTTP status của response.
            duration_ms: Thời gian xử lý tính bằng mili-giây.
            error: Exception nếu request thất bại (mặc định None).
        """
        message = "%s %s | name=%s | status=%s | %.2fms | ip=%s | ua=%s"
        args: list[Any] = [
            request.method,
            str(request.url),
            self._resolve_request_name(request),
            status_code,
            duration_ms,
            self._resolve_client_ip(request),
            self._resolve_user_agent(request),
        ]
        if error is not None:
            message += " | error=%s"
            args.append(f"{type(error).__name__}: {error}")
            logger.error(message, *args)
        else:
            logger.info(message, *args)

    def _resolve_request_name(self, request: Request) -> str:
        """Lấy tên request (route name), fallback về path.

        Args:
            request: Request cần lấy tên.

        Returns:
            Tên route nếu đã match, ngược lại là path của request.
        """
        route = request.scope.get("route")
        if route is not None:
            return getattr(route, "name", None) or getattr(route, "path", "unknown")
        return request.url.path

    def _resolve_client_ip(self, request: Request) -> str:
        """Lấy IP client, ưu tiên `X-Forwarded-For` khi đi qua proxy.

        Args:
            request: Request cần lấy IP.

        Returns:
            IP client hoặc "unknown" nếu không xác định được.
        """
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client is not None:
            return request.client.host
        return "unknown"

    def _resolve_user_agent(self, request: Request) -> str:
        """Lấy user-agent của client.

        Args:
            request: Request cần lấy user-agent.

        Returns:
            Chuỗi user-agent hoặc "unknown" nếu không có.
        """
        return request.headers.get("user-agent", "unknown")
