"""TicketTag 关联模型"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.sql import func

from app.database import Base


class TicketTag(Base):
    """Ticket 和 Tag 的多对多关联表"""

    __tablename__ = "ticket_tags"

    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 联合主键
    __table_args__ = (
        PrimaryKeyConstraint("ticket_id", "tag_id"),
    )

    def __repr__(self) -> str:
        return f"<TicketTag(ticket_id={self.ticket_id}, tag_id={self.tag_id})>"
