"""Tag 模型"""

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Tag(Base):
    """Tag 数据模型"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=False, default="#6B7280")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    tickets = relationship("Ticket", secondary="ticket_tags", back_populates="tags")

    # 使用 SQLite 兼容的约束（用于测试和开发）
    # 在生产环境的 PostgreSQL 中，Alembic 迁移会使用正则表达式约束
    # SQLite 不支持正则表达式，所以使用简单的字符串检查
    __table_args__ = (
        CheckConstraint(
            "color LIKE '#______' AND LENGTH(color) = 7",
            name="color_format",
        ),
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', color='{self.color}')>"
