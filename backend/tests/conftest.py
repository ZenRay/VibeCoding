"""pytest 配置和 fixtures"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# 导入所有模型以确保它们被注册到 Base.metadata
from app.models import Tag, Ticket, TicketTag  # noqa: F401

# 测试数据库 URL（使用文件数据库，避免内存数据库的连接问题）
# 使用固定路径，确保所有连接使用同一个数据库
_temp_db_path = os.path.join(tempfile.gettempdir(), "test_ticket_db.db")
# 如果文件存在，先删除
if os.path.exists(_temp_db_path):
    os.remove(_temp_db_path)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{_temp_db_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLite 不支持某些 PostgreSQL 特性，需要处理
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """设置 SQLite 的 PRAGMA"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """在每个测试前创建表，测试后清理数据"""
    # 确保模型已导入并注册到 Base.metadata
    # 创建所有表（如果不存在）
    Base.metadata.create_all(bind=engine)
    yield
    # 清理所有数据但保留表结构（更快）
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
