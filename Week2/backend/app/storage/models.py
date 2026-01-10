"""本地存储 SQLAlchemy 模型 - 使用 UTC 时间"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


def utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""

    pass


class DatabaseConnection(Base):
    """数据库连接存储模型"""

    __tablename__ = "database_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    db_type: Mapped[str] = mapped_column(String(50), nullable=False)  # postgresql, mysql, sqlite
    url: Mapped[str] = mapped_column(Text, nullable=False)  # 完整连接 URL（明文存储）
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    database: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # 关联元数据缓存
    metadata_cache: Mapped["MetadataCache | None"] = relationship(
        "MetadataCache",
        back_populates="connection",
        cascade="all, delete-orphan",
        uselist=False,
    )


class MetadataCache(Base):
    """元数据缓存存储模型"""

    __tablename__ = "metadata_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON 序列化的元数据
    version_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256 哈希
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    cached_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # 关联数据库连接
    connection: Mapped["DatabaseConnection"] = relationship(
        "DatabaseConnection", back_populates="metadata_cache"
    )

    __table_args__ = (Index("idx_metadata_connection", "connection_id"),)
