"""Ticket API 集成测试"""

import pytest
from datetime import datetime

from app.models import Ticket, Tag


class TestTicketAPI:
    """Ticket API 测试类"""

    def test_get_tickets_empty(self, client):
        """测试获取空 Ticket 列表"""
        response = client.get("/api/v1/tickets")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 0

    def test_create_ticket(self, client, db):
        """测试创建 Ticket"""
        response = client.post(
            "/api/v1/tickets",
            json={
                "title": "API 测试 Ticket",
                "description": "通过 API 创建的测试 Ticket",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "API 测试 Ticket"
        assert data["status"] == "pending"
        assert data["id"] is not None

    def test_get_ticket_by_id(self, client, db):
        """测试获取单个 Ticket"""
        # 先创建 Ticket
        ticket = Ticket(title="测试", status="pending")
        db.add(ticket)
        db.commit()

        response = client.get(f"/api/v1/tickets/{ticket.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket.id
        assert data["title"] == "测试"

    def test_get_ticket_not_found(self, client):
        """测试获取不存在的 Ticket"""
        response = client.get("/api/v1/tickets/999")
        assert response.status_code == 404

    def test_update_ticket(self, client, db):
        """测试更新 Ticket"""
        ticket = Ticket(title="原始标题", status="pending")
        db.add(ticket)
        db.commit()

        response = client.put(
            f"/api/v1/tickets/{ticket.id}",
            json={"title": "更新后的标题"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"

    def test_delete_ticket_soft(self, client, db):
        """测试软删除 Ticket"""
        ticket = Ticket(title="待删除", status="pending")
        db.add(ticket)
        db.commit()

        response = client.delete(f"/api/v1/tickets/{ticket.id}")
        assert response.status_code == 204

        # 验证已软删除
        db.refresh(ticket)
        assert ticket.deleted_at is not None

    def test_toggle_ticket_status(self, client, db):
        """测试切换 Ticket 状态"""
        ticket = Ticket(title="测试", status="pending")
        db.add(ticket)
        db.commit()

        response = client.patch(f"/api/v1/tickets/{ticket.id}/toggle-status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_create_ticket_with_tags(self, client, db):
        """测试创建带标签的 Ticket"""
        # 先创建标签
        tag1 = Tag(name="API_TEST1", color="#FF0000")
        tag2 = Tag(name="API_TEST2", color="#00FF00")
        db.add(tag1)
        db.add(tag2)
        db.commit()

        response = client.post(
            "/api/v1/tickets",
            json={
                "title": "带标签的 Ticket",
                "tag_ids": [tag1.id, tag2.id],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 2

    def test_add_tag_to_ticket(self, client, db):
        """测试为 Ticket 添加标签"""
        ticket = Ticket(title="测试", status="pending")
        tag = Tag(name="NEW_TAG", color="#0000FF")
        db.add(ticket)
        db.add(tag)
        db.commit()

        response = client.post(
            f"/api/v1/tickets/{ticket.id}/tags",
            json={"tag_id": tag.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == tag.id

    def test_remove_tag_from_ticket(self, client, db):
        """测试从 Ticket 移除标签"""
        from app.services.ticket_service import TicketService
        
        ticket = Ticket(title="测试", status="pending")
        tag = Tag(name="TO_REMOVE", color="#FF0000")
        db.add(ticket)
        db.add(tag)
        db.commit()

        # 先添加标签
        TicketService.add_tag_to_ticket(db, ticket.id, tag.id)

        # 移除标签
        response = client.delete(f"/api/v1/tickets/{ticket.id}/tags/{tag.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 0
