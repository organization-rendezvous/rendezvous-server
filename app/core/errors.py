class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다.") -> None:
        super().__init__("NOT_FOUND", message, 404)


class StorageError(AppError):
    def __init__(self, message: str = "데이터 저장 중 오류가 발생했습니다.") -> None:
        super().__init__("STORAGE_ERROR", message, 500)
