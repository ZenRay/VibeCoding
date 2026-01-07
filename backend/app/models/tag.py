"""Tag 模型"""

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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

    # 约束
    __table_args__ = (
        CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="color_format"),
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', color='{self.color}')>"
