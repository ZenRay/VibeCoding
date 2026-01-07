"""Ticket Service 单元测试"""

import pytest
from datetime import datetime

from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketQueryParams
from app.models import Ticket, Tag
from app.utils.exceptions import NotFoundError, ValidationError


class TestTicketService:
    """Ticket Service 测试类"""

    def test_create_ticket(self, db):
        """测试创建 Ticket"""
        ticket_data = TicketCreate(
            title="测试 Ticket",
            description="这是一个测试",
        )
        ticket = TicketService.create_ticket(db, ticket_data)

        assert ticket.id is not None
        assert ticket.title == "测试 Ticket"
        assert ticket.description == "这是一个测试"
        assert ticket.status == "pending"
        assert ticket.deleted_at is None

    def test_create_ticket_with_tags(self, db):
        """测试创建带标签的 Ticket"""
        # 先创建标签
        tag1 = Tag(name="TEST1", color="#FF0000")
        tag2 = Tag(name="TEST2", color="#00FF00")
        db.add(tag1)
        db.add(tag2)
        db.commit()

        ticket_data = TicketCreate(
            title="带标签的 Ticket",
            tag_ids=[tag1.id, tag2.id],
        )
        ticket = TicketService.create_ticket(db, ticket_data)

        assert len(ticket.tags) == 2
        assert tag1.id in [t.id for t in ticket.tags]
        assert tag2.id in [t.id for t in ticket.tags]

    def test_get_ticket_by_id(self, db):
        """测试根据 ID 获取 Ticket"""
        ticket = Ticket(
            title="测试 Ticket",
            description="测试描述",
            status="pending",
        )
        db.add(ticket)
        db.commit()

        found_ticket = TicketService.get_ticket_by_id(db, ticket.id)
        assert found_ticket.id == ticket.id
        assert found_ticket.title == "测试 Ticket"

    def test_get_ticket_not_found(self, db):
        """测试获取不存在的 Ticket"""
        with pytest.raises(NotFoundError):
            TicketService.get_ticket_by_id(db, 999)

    def test_update_ticket(self, db):
        """测试更新 Ticket"""
        ticket = Ticket(title="原始标题", description="原始描述", status="pending")
        db.add(ticket)
        db.commit()

        update_data = TicketUpdate(title="更新后的标题")
        updated_ticket = TicketService.update_ticket(db, ticket.id, update_data)

        assert updated_ticket.title == "更新后的标题"
        assert updated_ticket.description == "原始描述"

    def test_delete_ticket_soft(self, db):
        """测试软删除 Ticket"""
        ticket = Ticket(title="待删除", status="pending")
        db.add(ticket)
        db.commit()

        TicketService.delete_ticket(db, ticket.id, permanent=False)
        db.refresh(ticket)

        assert ticket.deleted_at is not None

    def test_delete_ticket_permanent(self, db):
        """测试永久删除 Ticket"""
        ticket = Ticket(title="待删除", status="pending")
        db.add(ticket)
        db.commit()
        ticket_id = ticket.id

        TicketService.delete_ticket(db, ticket_id, permanent=True)

        found_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        assert found_ticket is None

    def test_restore_ticket(self, db):
        """测试恢复 Ticket"""
        ticket = Ticket(title="待恢复", status="pending", deleted_at=datetime.utcnow())
        db.add(ticket)
        db.commit()

        restored_ticket = TicketService.restore_ticket(db, ticket.id)
        assert restored_ticket.deleted_at is None

    def test_toggle_ticket_status(self, db):
        """测试切换 Ticket 状态"""
        ticket = Ticket(title="测试", status="pending")
        db.add(ticket)
        db.commit()

        # pending -> completed
        updated = TicketService.toggle_ticket_status(db, ticket.id)
        assert updated.status == "completed"

        # completed -> pending
        updated = TicketService.toggle_ticket_status(db, ticket.id)
        assert updated.status == "pending"

    def test_add_tag_to_ticket(self, db):
        """测试为 Ticket 添加标签"""
        ticket = Ticket(title="测试", status="pending")
        tag = Tag(name="TEST", color="#FF0000")
        db.add(ticket)
        db.add(tag)
        db.commit()

        updated_ticket = TicketService.add_tag_to_ticket(db, ticket.id, tag.id)
        assert len(updated_ticket.tags) == 1
        assert updated_ticket.tags[0].id == tag.id

    def test_remove_tag_from_ticket(self, db):
        """测试从 Ticket 移除标签"""
        ticket = Ticket(title="测试", status="pending")
        tag = Tag(name="TEST", color="#FF0000")
        db.add(ticket)
        db.add(tag)
        db.commit()

        # 添加标签
        TicketService.add_tag_to_ticket(db, ticket.id, tag.id)

        # 移除标签
        updated_ticket = TicketService.remove_tag_from_ticket(db, ticket.id, tag.id)
        assert len(updated_ticket.tags) == 0
