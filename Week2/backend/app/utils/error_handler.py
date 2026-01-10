"""错误处理和错误响应模型"""

from enum import Enum
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ErrorCode(str, Enum):
    """错误代码枚举"""

    # 连接错误
    CONNECTION_FAILED = "CONNECTION_FAILED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    DATABASE_NOT_FOUND = "DATABASE_NOT_FOUND"
    NETWORK_UNREACHABLE = "NETWORK_UNREACHABLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # 查询错误
    QUERY_TIMEOUT = "QUERY_TIMEOUT"
    QUERY_CANCELLED = "QUERY_CANCELLED"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INVALID_STATEMENT = "INVALID_STATEMENT"
    CONFLICT = "CONFLICT"  # 并发冲突

    # AI 服务错误
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"

    # 存储错误
    STORAGE_FULL = "STORAGE_FULL"
    STORAGE_CORRUPTED = "STORAGE_CORRUPTED"

    # 通用错误
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """错误响应模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: ErrorCode = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: dict[str, Any] | None = Field(None, description="详细信息")


class ValidationErrorDetail(BaseModel):
    """验证错误详情"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误信息")
    value: Any = Field(None, description="错误值")


def create_error_response(
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTTPException:
    """创建错误响应"""
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            code=code,
            message=message,
            details=details,
        ).model_dump(),
    )


# 错误代码到 HTTP 状态码的映射
ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.CONNECTION_FAILED: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.AUTHENTICATION_FAILED: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.QUERY_TIMEOUT: status.HTTP_408_REQUEST_TIMEOUT,
    ErrorCode.QUERY_CANCELLED: status.HTTP_400_BAD_REQUEST,  # 使用 400 代替 499
    ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,  # 并发冲突
    ErrorCode.AI_SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.AI_QUOTA_EXCEEDED: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}
