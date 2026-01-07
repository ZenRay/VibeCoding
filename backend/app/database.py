"""数据库连接和会话管理"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_size=10,
    max_overflow=20,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖注入函数

    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
