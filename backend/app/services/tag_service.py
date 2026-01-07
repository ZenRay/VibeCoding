"""Tag 业务逻辑服务"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Tag, TicketTag
from app.schemas.tag import TagCreate, TagUpdate
from app.utils.exceptions import NotFoundError, ConflictError


class TagService:
    """Tag 服务类"""

    @staticmethod
    def get_tags(
        db: Session,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> List[Tag]:
        """
        获取标签列表（支持排序）

        Args:
            db: 数据库会话
            sort_by: 排序字段（name, created_at, usage_count）
            sort_order: 排序顺序（asc, desc）

        Returns:
            List[Tag]: 标签列表
        """
        query = db.query(Tag)

        # 根据排序字段排序
        if sort_by == "usage_count":
            # 按使用次数排序（需要子查询统计）
            subquery = (
                db.query(
                    TicketTag.tag_id,
                    func.count(TicketTag.ticket_id).label("count"),
                )
                .group_by(TicketTag.tag_id)
                .subquery()
            )
            query = query.outerjoin(
                subquery, Tag.id == subquery.c.tag_id
            ).order_by(
                func.coalesce(subquery.c.count, 0).desc()
                if sort_order == "desc"
                else func.coalesce(subquery.c.count, 0).asc()
            )
        elif sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(Tag.created_at.desc())
            else:
                query = query.order_by(Tag.created_at.asc())
        else:  # name
            if sort_order == "desc":
                query = query.order_by(Tag.name.desc())
            else:
                query = query.order_by(Tag.name.asc())

        tags = query.all()

        # 为每个标签添加使用次数统计
        for tag in tags:
            tag.ticket_count = (
                db.query(func.count(TicketTag.ticket_id))
                .filter(TicketTag.tag_id == tag.id)
                .scalar()
            )

        return tags

    @staticmethod
    def get_tag_by_id(
        db: Session,
        tag_id: int,
    ) -> Tag:
        """
        根据 ID 获取单个标签

        Args:
            db: 数据库会话
            tag_id: Tag ID

        Returns:
            Tag: Tag 对象

        Raises:
            NotFoundError: Tag 不存在
        """
        tag = db.query(Tag).filter(Tag.id == tag_id).first()

        if not tag:
            raise NotFoundError(f"标签 ID {tag_id} 不存在")

        # 添加使用次数统计
        tag.ticket_count = (
            db.query(func.count(TicketTag.ticket_id))
            .filter(TicketTag.tag_id == tag_id)
            .scalar()
        )

        return tag

    @staticmethod
    def get_tag_by_name(
        db: Session,
        name: str,
    ) -> Optional[Tag]:
        """
        根据名称查找标签（用于去重）

        Args:
            db: 数据库会话
            name: 标签名称

        Returns:
            Optional[Tag]: Tag 对象，如果不存在则返回 None
        """
        # 注意：数据库触发器会自动将名称转换为大写
        # 所以这里也需要转换为大写进行查询
        normalized_name = name.strip().upper()
        return db.query(Tag).filter(func.upper(Tag.name) == normalized_name).first()

    @staticmethod
    def create_tag(
        db: Session,
        tag_data: TagCreate,
    ) -> Tag:
        """
        创建新标签

        Args:
            db: 数据库会话
            tag_data: Tag 创建数据

        Returns:
            Tag: 创建的 Tag 对象

        Raises:
            ConflictError: 标签名称已存在
        """
        # 检查标签是否已存在（数据库触发器会自动标准化名称）
        existing_tag = TagService.get_tag_by_name(db, tag_data.name)
        if existing_tag:
            raise ConflictError(f"标签名称 '{tag_data.name}' 已存在")

        # 创建标签（触发器会自动标准化名称）
        tag = Tag(
            name=tag_data.name,
            color=tag_data.color,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)

        tag.ticket_count = 0
        return tag

    @staticmethod
    def update_tag(
        db: Session,
        tag_id: int,
        tag_data: TagUpdate,
    ) -> Tag:
        """
        更新标签

        Args:
            db: 数据库会话
            tag_id: Tag ID
            tag_data: Tag 更新数据

        Returns:
            Tag: 更新后的 Tag 对象

        Raises:
            NotFoundError: Tag 不存在
            ConflictError: 新标签名称已存在
        """
        tag = db.query(Tag).filter(Tag.id == tag_id).first()

        if not tag:
            raise NotFoundError(f"标签 ID {tag_id} 不存在")

        # 如果更新名称，检查是否冲突
        if tag_data.name is not None and tag_data.name != tag.name:
            existing_tag = TagService.get_tag_by_name(db, tag_data.name)
            if existing_tag and existing_tag.id != tag_id:
                raise ConflictError(f"标签名称 '{tag_data.name}' 已存在")

        # 更新字段
        if tag_data.name is not None:
            tag.name = tag_data.name
        if tag_data.color is not None:
            tag.color = tag_data.color

        db.commit()
        db.refresh(tag)

        # 添加使用次数统计
        tag.ticket_count = (
            db.query(func.count(TicketTag.ticket_id))
            .filter(TicketTag.tag_id == tag_id)
            .scalar()
        )

        return tag

    @staticmethod
    def delete_tag(
        db: Session,
        tag_id: int,
    ) -> None:
        """
        删除标签

        Args:
            db: 数据库会话
            tag_id: Tag ID

        Raises:
            NotFoundError: Tag 不存在
        """
        tag = db.query(Tag).filter(Tag.id == tag_id).first()

        if not tag:
            raise NotFoundError(f"标签 ID {tag_id} 不存在")

        # 删除标签（关联关系会通过 CASCADE 自动删除）
        db.delete(tag)
        db.commit()
