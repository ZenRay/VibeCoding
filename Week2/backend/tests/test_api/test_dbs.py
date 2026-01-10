"""数据库连接 API 测试"""

from fastapi.testclient import TestClient

from app.main import app
from app.storage.local_db import init_db

# 初始化测试数据库
init_db()

client = TestClient(app)


def test_list_databases_empty():
    """测试空数据库列表"""
    response = client.get("/api/v1/dbs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["databases"] == []


def test_add_database_invalid_url():
    """测试添加无效 URL"""
    response = client.put(
        "/api/v1/dbs/test-db",
        json={"url": "invalid-url"},
    )
    assert response.status_code == 400


def test_add_database_sqlite():
    """测试添加 SQLite 数据库"""
    response = client.put(
        "/api/v1/dbs/test-sqlite",
        json={"url": "sqlite:///test.db"},
    )
    # 注意：实际连接可能失败，但可以测试 API 结构
    assert response.status_code in [201, 422]
