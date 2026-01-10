"""本地 SQLite 存储操作层 - 使用 UTC 时间"""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.storage.models import Base, DatabaseConnection, MetadataCache


def utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(UTC)


# 创建数据库引擎
def get_database_path() -> Path:
    """获取数据库文件路径"""
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        # 提取路径部分
        path_str = db_url.replace("sqlite:///", "")
        # 解析相对路径（相对于 backend 目录）
        path = Path(path_str)
        if not path.is_absolute():
            # 相对于 backend 目录
            backend_dir = Path(__file__).parent.parent.parent
            # 处理 ../ 相对路径
            if path_str.startswith("../"):
                path = (backend_dir.parent / path_str.replace("../", "")).resolve()
            else:
                path = (backend_dir / path_str).resolve()
        return path
    raise ValueError(f"不支持的数据库 URL: {db_url}")


def ensure_database_directory() -> None:
    """确保数据库目录存在"""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)


# 创建引擎和会话工厂
ensure_database_directory()
db_path = get_database_path()
engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},  # SQLite 需要这个参数
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """初始化数据库（创建表）"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LocalStorage:
    """本地存储操作类"""

    @staticmethod
    def get_connection_by_name(db: Session, name: str) -> DatabaseConnection | None:
        """根据名称获取连接"""

        stmt = select(DatabaseConnection).where(DatabaseConnection.name == name)
        return db.scalar(stmt)

    @staticmethod
    def get_all_connections(db: Session) -> list[DatabaseConnection]:
        """获取所有连接（按创建时间降序）"""
        from sqlalchemy import desc

        stmt = select(DatabaseConnection).order_by(desc(DatabaseConnection.created_at))
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_connection(
        db: Session,
        name: str,
        db_type: str,
        url: str,
        host: str | None = None,
        port: int | None = None,
        database: str = "",
    ) -> DatabaseConnection:
        """创建新连接"""
        conn = DatabaseConnection(
            name=name,
            db_type=db_type,
            url=url,
            host=host,
            port=port,
            database=database,
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)
        return conn

    @staticmethod
    def update_connection(
        db: Session,
        connection: DatabaseConnection,
        url: str,
        host: str | None = None,
        port: int | None = None,
        database: str = "",
    ) -> DatabaseConnection:
        """更新连接"""
        connection.url = url
        connection.host = host
        connection.port = port
        connection.database = database
        connection.updated_at = utc_now()
        db.commit()
        db.refresh(connection)
        return connection

    @staticmethod
    def delete_connection(db: Session, connection: DatabaseConnection) -> None:
        """删除连接（级联删除元数据缓存）"""
        db.delete(connection)
        db.commit()

    @staticmethod
    def get_metadata_cache(
        db: Session,
        connection_id: int,
    ) -> MetadataCache | None:
        """获取元数据缓存"""
        stmt = select(MetadataCache).where(MetadataCache.connection_id == connection_id)
        return db.scalar(stmt)

    @staticmethod
    def save_metadata_cache(
        db: Session,
        connection_id: int,
        metadata_json: str,
        version_hash: str | None = None,
    ) -> MetadataCache:
        """保存或更新元数据缓存"""
        cache = LocalStorage.get_metadata_cache(db, connection_id)

        if cache:
            # 更新现有缓存
            cache.metadata_json = metadata_json
            cache.version_hash = version_hash
            cache.size_bytes = len(metadata_json.encode("utf-8"))
            cache.cached_at = utc_now()
        else:
            # 创建新缓存
            cache = MetadataCache(
                connection_id=connection_id,
                metadata_json=metadata_json,
                version_hash=version_hash,
                size_bytes=len(metadata_json.encode("utf-8")),
            )
            db.add(cache)

        db.commit()
        db.refresh(cache)
        return cache

    @staticmethod
    def delete_metadata_cache(db: Session, connection_id: int) -> None:
        """删除元数据缓存"""
        cache = LocalStorage.get_metadata_cache(db, connection_id)
        if cache:
            db.delete(cache)
            db.commit()
