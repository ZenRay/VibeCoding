"""响应工具函数"""

from typing import Any, Optional


def success_response(data: Any = None, message: str = "Success") -> dict:
    """
    成功响应格式

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        dict: 格式化的响应字典
    """
    response = {"message": message}
    if data is not None:
        response["data"] = data
    return response


def error_response(code: str, message: str, details: Optional[dict] = None) -> dict:
    """
    错误响应格式

    Args:
        code: 错误代码
        message: 错误消息
        details: 错误详情

    Returns:
        dict: 格式化的错误响应字典
    """
    response = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        response["error"]["details"] = details
    return response
