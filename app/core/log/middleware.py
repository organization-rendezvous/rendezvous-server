from __future__ import annotations
import time
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.log.logging_config import get_access_logger, get_error_logger

error_logger = get_error_logger()


def _extract_api_name(path: str) -> str:
    """경로에서 API 이름 추출. /api/trends/... → trends"""
    parts = [p for p in path.split("/") if p]
    # parts 예: ["api", "trends", "analyze"]
    if len(parts) >= 2:
        return parts[1]
    return "unknown"


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_name = _extract_api_name(request.url.path)
        access_logger = get_access_logger(api_name)

        # 쿼리/패스 파라미터만 기록 (바디는 너무 커질 수 있어 생략)
        params = dict(request.query_params)

        start = time.time()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            access_logger.info(
                "%s %s | params=%s | status=FAIL | %dms | exception",
                request.method,
                request.url.path,
                params,
                duration_ms,
            )
            error_logger.error(
                "%s %s | params=%s | %s\n%s",
                request.method,
                request.url.path,
                params,
                str(exc),
                traceback.format_exc(),
            )
            raise  # FastAPI 예외 핸들러가 마저 처리하도록 재발생

        duration_ms = int((time.time() - start) * 1000)
        status = "SUCCESS" if response.status_code < 400 else "FAIL"

        access_logger.info(
            "%s %s | params=%s | status=%s | %d | %dms",
            request.method,
            request.url.path,
            params,
            status,
            response.status_code,
            duration_ms,
        )

        if status == "FAIL":
            error_logger.error(
                "%s %s | params=%s | http_status=%d",
                request.method,
                request.url.path,
                params,
                response.status_code,
            )

        return response