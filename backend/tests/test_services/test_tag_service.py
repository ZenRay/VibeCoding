"""Tag Service 单元测试"""

import pytest

from app.services.tag_service import TagService
from app.schemas.tag import TagCreate, TagUpdate
from app.models import Tag
from app.utils.exceptions import NotFoundError, ConflictError


class TestTagService:
    """Tag Service 测试类"""

    def test_create_tag(self, db):
        """测试创建标签"""
        tag_data = TagCreate(name="TEST", color="#FF0000")
        tag = TagService.create_tag(db, tag_data)

        assert tag.id is not None
        assert tag.name == "TEST"  # 注意：数据库触发器会自动转大写
        assert tag.color == "#FF0000"

    def test_create_tag_duplicate(self, db):
        """测试创建重复标签"""
        tag_data = TagCreate(name="TEST", color="#FF0000")
        TagService.create_tag(db, tag_data)

        # 尝试创建同名标签（不同大小写）
        with pytest.raises(ConflictError):
            TagService.create_tag(db, TagCreate(name="test", color="#00FF00"))

    def test_get_tag_by_id(self, db):
        """测试根据 ID 获取标签"""
        tag = Tag(name="TEST", color="#FF0000")
        db.add(tag)
        db.commit()

        found_tag = TagService.get_tag_by_id(db, tag.id)
        assert found_tag.id == tag.id
        assert found_tag.name == "TEST"

    def test_get_tag_not_found(self, db):
        """测试获取不存在的标签"""
        with pytest.raises(NotFoundError):
            TagService.get_tag_by_id(db, 999)

    def test_get_tag_by_name(self, db):
        """测试根据名称查找标签"""
        tag = Tag(name="TEST", color="#FF0000")
        db.add(tag)
        db.commit()

        found_tag = TagService.get_tag_by_name(db, "test")
        assert found_tag is not None
        assert found_tag.id == tag.id

    def test_update_tag(self, db):
        """测试更新标签"""
        tag = Tag(name="ORIGINAL", color="#FF0000")
        db.add(tag)
        db.commit()

        update_data = TagUpdate(name="UPDATED", color="#00FF00")
        updated_tag = TagService.update_tag(db, tag.id, update_data)

        assert updated_tag.name == "UPDATED"
        assert updated_tag.color == "#00FF00"

    def test_delete_tag(self, db):
        """测试删除标签"""
        tag = Tag(name="TO_DELETE", color="#FF0000")
        db.add(tag)
        db.commit()
        tag_id = tag.id

        TagService.delete_tag(db, tag_id)

        found_tag = db.query(Tag).filter(Tag.id == tag_id).first()
        assert found_tag is None
