"""Ticket 业务逻辑服务"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models import Ticket, Tag, TicketTag
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketQueryParams
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.pagination import paginate, PaginatedResult


class TicketService:
    """Ticket 服务类"""

    @staticmethod
    def get_tickets(
        db: Session,
        params: TicketQueryParams,
    ) -> PaginatedResult:
        """
        获取 Ticket 列表（支持过滤、搜索、分页）

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            PaginatedResult: 分页结果
        """
        query = db.query(Ticket)

        # 软删除过滤
        if params.only_deleted:
            query = query.filter(Ticket.deleted_at.isnot(None))
        elif not params.include_deleted:
            query = query.filter(Ticket.deleted_at.is_(None))

        # 状态过滤
        if params.status and params.status != "all":
            query = query.filter(Ticket.status == params.status)

        # 标签过滤
        if params.tag_ids:
            if params.tag_filter == "or":
                # OR 逻辑：包含任一标签
                query = query.join(TicketTag).filter(
                    TicketTag.tag_id.in_(params.tag_ids)
                ).distinct()
            else:
                # AND 逻辑：包含所有标签（默认）
                for tag_id in params.tag_ids:
                    subquery = (
                        db.query(TicketTag.ticket_id)
                        .filter(TicketTag.tag_id == tag_id)
                        .subquery()
                    )
                    query = query.filter(Ticket.id.in_(subquery))

        # 全文搜索
        if params.search:
            search_term = params.search.strip()
            if search_term:
                # 使用 LIKE 模糊搜索（兼容 SQLite 和 PostgreSQL）
                search_pattern = f"%{search_term}%"
                query = query.filter(Ticket.title.ilike(search_pattern))

        # 排序
        sort_by = params.sort_by or "created_at"
        sort_order = params.sort_order or "desc"

        if sort_by == "title":
            order_column = Ticket.title
        elif sort_by == "updated_at":
            order_column = Ticket.updated_at
        else:  # created_at
            order_column = Ticket.created_at

        if sort_order == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())

        # 分页
        page = params.page or 1
        page_size = params.page_size or 20

        return paginate(query, page=page, page_size=page_size)

    @staticmethod
    def get_ticket_by_id(
        db: Session,
        ticket_id: int,
        include_deleted: bool = False,
    ) -> Ticket:
        """
        根据 ID 获取单个 Ticket

        Args:
            db: 数据库会话
            ticket_id: Ticket ID
            include_deleted: 是否包含已删除的 Ticket

        Returns:
            Ticket: Ticket 对象

        Raises:
            NotFoundError: Ticket 不存在
        """
        query = db.query(Ticket).filter(Ticket.id == ticket_id)

        if not include_deleted:
            query = query.filter(Ticket.deleted_at.is_(None))

        ticket = query.first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        return ticket

    @staticmethod
    def create_ticket(
        db: Session,
        ticket_data: TicketCreate,
    ) -> Ticket:
        """
        创建新的 Ticket

        Args:
            db: 数据库会话
            ticket_data: Ticket 创建数据

        Returns:
            Ticket: 创建的 Ticket 对象
        """
        # 创建 Ticket
        ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            status="pending",
        )
        db.add(ticket)
        db.flush()  # 获取 ticket.id

        # 添加标签关联
        if ticket_data.tag_ids:
            for tag_id in ticket_data.tag_ids:
                # 验证标签是否存在
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if not tag:
                    raise NotFoundError(f"标签 ID {tag_id} 不存在")

                ticket_tag = TicketTag(ticket_id=ticket.id, tag_id=tag_id)
                db.add(ticket_tag)

        db.commit()
        db.refresh(ticket)

        # 重新加载以获取标签关系
        return db.query(Ticket).filter(Ticket.id == ticket.id).first()

    @staticmethod
    def update_ticket(
        db: Session,
        ticket_id: int,
        ticket_data: TicketUpdate,
    ) -> Ticket:
        """
        更新 Ticket

        Args:
            db: 数据库会话
            ticket_id: Ticket ID
            ticket_data: Ticket 更新数据

        Returns:
            Ticket: 更新后的 Ticket 对象

        Raises:
            NotFoundError: Ticket 不存在
        """
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.deleted_at.is_(None),
        ).first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        # 更新字段
        if ticket_data.title is not None:
            ticket.title = ticket_data.title
        if ticket_data.description is not None:
            ticket.description = ticket_data.description

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def delete_ticket(
        db: Session,
        ticket_id: int,
        permanent: bool = False,
    ) -> None:
        """
        删除 Ticket（软删除或永久删除）

        Args:
            db: 数据库会话
            ticket_id: Ticket ID
            permanent: 是否永久删除

        Raises:
            NotFoundError: Ticket 不存在
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        if permanent:
            # 永久删除
            db.delete(ticket)
        else:
            # 软删除
            ticket.deleted_at = datetime.utcnow()

        db.commit()

    @staticmethod
    def restore_ticket(
        db: Session,
        ticket_id: int,
    ) -> Ticket:
        """
        恢复已删除的 Ticket

        Args:
            db: 数据库会话
            ticket_id: Ticket ID

        Returns:
            Ticket: 恢复后的 Ticket 对象

        Raises:
            NotFoundError: Ticket 不存在或未被删除
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        if ticket.deleted_at is None:
            raise ValidationError("Ticket 未被删除，无需恢复")

        ticket.deleted_at = None
        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def toggle_ticket_status(
        db: Session,
        ticket_id: int,
    ) -> Ticket:
        """
        切换 Ticket 完成状态

        Args:
            db: 数据库会话
            ticket_id: Ticket ID

        Returns:
            Ticket: 更新后的 Ticket 对象

        Raises:
            NotFoundError: Ticket 不存在
        """
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.deleted_at.is_(None),
        ).first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        # 切换状态
        if ticket.status == "pending":
            ticket.status = "completed"
        else:
            ticket.status = "pending"

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def add_tag_to_ticket(
        db: Session,
        ticket_id: int,
        tag_id: int,
    ) -> Ticket:
        """
        为 Ticket 添加标签

        Args:
            db: 数据库会话
            ticket_id: Ticket ID
            tag_id: Tag ID

        Returns:
            Ticket: 更新后的 Ticket 对象

        Raises:
            NotFoundError: Ticket 或 Tag 不存在
            ConflictError: 标签已存在
        """
        from app.utils.exceptions import ConflictError

        # 验证 Ticket 存在
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.deleted_at.is_(None),
        ).first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        # 验证 Tag 存在
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise NotFoundError(f"标签 ID {tag_id} 不存在")

        # 检查是否已存在关联
        existing = (
            db.query(TicketTag)
            .filter(
                TicketTag.ticket_id == ticket_id,
                TicketTag.tag_id == tag_id,
            )
            .first()
        )

        if existing:
            raise ConflictError("标签已关联到此 Ticket")

        # 创建关联
        ticket_tag = TicketTag(ticket_id=ticket_id, tag_id=tag_id)
        db.add(ticket_tag)
        db.commit()

        # 重新加载 Ticket
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()

    @staticmethod
    def remove_tag_from_ticket(
        db: Session,
        ticket_id: int,
        tag_id: int,
    ) -> Ticket:
        """
        从 Ticket 移除标签

        Args:
            db: 数据库会话
            ticket_id: Ticket ID
            tag_id: Tag ID

        Returns:
            Ticket: 更新后的 Ticket 对象

        Raises:
            NotFoundError: Ticket、Tag 或关联不存在
        """
        # 验证 Ticket 存在
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.deleted_at.is_(None),
        ).first()

        if not ticket:
            raise NotFoundError(f"Ticket ID {ticket_id} 不存在")

        # 查找并删除关联
        ticket_tag = (
            db.query(TicketTag)
            .filter(
                TicketTag.ticket_id == ticket_id,
                TicketTag.tag_id == tag_id,
            )
            .first()
        )

        if not ticket_tag:
            raise NotFoundError("标签未关联到此 Ticket")

        db.delete(ticket_tag)
        db.commit()

        # 重新加载 Ticket
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()
