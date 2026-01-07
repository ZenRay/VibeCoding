"""Ticket 模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Ticket(Base):
    """Ticket 数据模型"""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # 关系
    tags = relationship("Tag", secondary="ticket_tags", back_populates="tickets")

    # 约束
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'completed')", name="status_check"),
    )

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, title='{self.title}', status='{self.status}')>"
