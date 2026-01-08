"""分页工具函数"""

from math import ceil
from typing import TypeVar

from sqlalchemy.orm import Query

T = TypeVar("T")


class PaginatedResult[T]:
    """分页结果"""

    def __init__(self, items: list[T], total: int, page: int, page_size: int):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = ceil(total / page_size) if page_size > 0 else 0

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "data": self.items,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "total_pages": self.total_pages,
            },
        }


def paginate(
    query: Query, page: int = 1, page_size: int = 20, max_page_size: int = 100
) -> PaginatedResult:
    """
    对查询结果进行分页

    Args:
        query: SQLAlchemy 查询对象
        page: 页码（从 1 开始）
        page_size: 每页数量
        max_page_size: 最大每页数量

    Returns:
        PaginatedResult: 分页结果对象
    """
    # 限制 page_size
    if page_size > max_page_size:
        page_size = max_page_size
    if page_size < 1:
        page_size = 20

    # 确保 page >= 1
    if page < 1:
        page = 1

    # 计算总数
    total = query.count()

    # 计算偏移量
    offset = (page - 1) * page_size

    # 获取分页数据
    items = query.offset(offset).limit(page_size).all()

    return PaginatedResult(items=items, total=total, page=page, page_size=page_size)
