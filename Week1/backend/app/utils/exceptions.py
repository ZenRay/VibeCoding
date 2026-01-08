"""自定义异常类"""


class BaseAPIException(Exception):
    """API 异常基类"""

    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(BaseAPIException):
    """资源未找到异常"""

    def __init__(self, message: str = "资源未找到", details: dict = None):
        super().__init__(message, "NOT_FOUND", details)


class ValidationError(BaseAPIException):
    """验证错误异常"""

    def __init__(self, message: str = "验证失败", details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class ConflictError(BaseAPIException):
    """资源冲突异常"""

    def __init__(self, message: str = "资源冲突", details: dict = None):
        super().__init__(message, "CONFLICT", details)
