from __future__ import annotations
import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_ROOT = "logs"
ACCESS_DIR = os.path.join(LOG_ROOT, "access")
ERROR_DIR = os.path.join(LOG_ROOT, "errors")

os.makedirs(ACCESS_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)

ACCESS_FORMAT = "%(asctime)s | %(name)s | %(message)s"
ERROR_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

_access_loggers: dict[str, logging.Logger] = {}


def get_access_logger(api_name: str) -> logging.Logger:
    """API별 access 로거. 같은 이름이면 캐시된 인스턴스 재사용."""
    if api_name in _access_loggers:
        return _access_loggers[api_name]

    logger = logging.getLogger(f"access.{api_name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 루트 로거(콘솔)로 전파 안 함

    handler = TimedRotatingFileHandler(
        filename=os.path.join(ACCESS_DIR, f"{api_name}.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(ACCESS_FORMAT))
    logger.addHandler(handler)

    _access_loggers[api_name] = logger
    return logger


def get_error_logger() -> logging.Logger:
    """모든 API 공통 에러 로거. 한 파일에 모아서 기록."""
    logger = logging.getLogger("errors")
    if logger.handlers:
        return logger

    logger.setLevel(logging.ERROR)
    logger.propagate = False

    handler = TimedRotatingFileHandler(
        filename=os.path.join(ERROR_DIR, "errors.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(ERROR_FORMAT))
    logger.addHandler(handler)

    return logger