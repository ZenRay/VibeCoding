"""数据库适配器基类"""

from abc import ABC, abstractmethod
from typing import Any


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    @abstractmethod
    async def connect(self, url: str) -> None:
        """建立数据库连接"""
        pass

    @abstractmethod
    async def execute(
        self,
        sql: str,
        timeout: float = 30.0,
    ) -> list[dict[str, Any]]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 查询语句（必须是 SELECT）
            timeout: 超时时间（秒）

        Returns:
            查询结果列表（每行是一个字典）
        """
        pass

    @abstractmethod
    async def get_metadata(self) -> dict[str, Any]:
        """
        获取数据库元数据

        Returns:
            包含 tables 和 views 的字典
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭数据库连接"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接是否有效"""
        pass
