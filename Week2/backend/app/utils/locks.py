"""并发控制 - 互斥锁管理"""

import asyncio

# 模块级别的互斥锁
_metadata_refresh_lock: asyncio.Lock | None = None
_query_execution_lock: asyncio.Lock | None = None


def get_metadata_lock() -> asyncio.Lock:
    """获取元数据刷新锁"""
    global _metadata_refresh_lock
    if _metadata_refresh_lock is None:
        _metadata_refresh_lock = asyncio.Lock()
    return _metadata_refresh_lock


def get_query_lock() -> asyncio.Lock:
    """获取查询执行锁"""
    global _query_execution_lock
    if _query_execution_lock is None:
        _query_execution_lock = asyncio.Lock()
    return _query_execution_lock


def is_metadata_refreshing() -> bool:
    """检查元数据是否正在刷新"""
    lock = get_metadata_lock()
    return lock.locked()


def is_query_executing() -> bool:
    """检查查询是否正在执行"""
    lock = get_query_lock()
    return lock.locked()
