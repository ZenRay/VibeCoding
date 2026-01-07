"""Tag API 集成测试"""


from app.models import Tag


class TestTagAPI:
    """Tag API 测试类"""

    def test_get_tags_empty(self, client):
        """测试获取空标签列表"""
        response = client.get("/api/v1/tags")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 0

    def test_create_tag(self, client):
        """测试创建标签"""
        response = client.post(
            "/api/v1/tags",
            json={
                "name": "api_test",
                "color": "#FF0000",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API_TEST"  # 注意：数据库触发器会自动转大写
        assert data["color"] == "#FF0000"
        assert data["id"] is not None

    def test_create_tag_duplicate(self, client, db):
        """测试创建重复标签"""
        tag = Tag(name="DUPLICATE", color="#FF0000")
        db.add(tag)
        db.commit()

        response = client.post(
            "/api/v1/tags",
            json={
                "name": "duplicate",  # 不同大小写
                "color": "#00FF00",
            },
        )
        assert response.status_code == 409  # 冲突

    def test_get_tag_by_id(self, client, db):
        """测试获取单个标签"""
        tag = Tag(name="API_TEST", color="#FF0000")
        db.add(tag)
        db.commit()

        response = client.get(f"/api/v1/tags/{tag.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tag.id
        assert data["name"] == "API_TEST"

    def test_get_tag_not_found(self, client):
        """测试获取不存在的标签"""
        response = client.get("/api/v1/tags/999")
        assert response.status_code == 404

    def test_update_tag(self, client, db):
        """测试更新标签"""
        tag = Tag(name="ORIGINAL", color="#FF0000")
        db.add(tag)
        db.commit()

        response = client.put(
            f"/api/v1/tags/{tag.id}",
            json={
                "name": "updated",
                "color": "#00FF00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UPDATED"  # 自动转大写
        assert data["color"] == "#00FF00"

    def test_delete_tag(self, client, db):
        """测试删除标签"""
        tag = Tag(name="TO_DELETE", color="#FF0000")
        db.add(tag)
        db.commit()

        response = client.delete(f"/api/v1/tags/{tag.id}")
        assert response.status_code == 204

        # 验证已删除
        response = client.get(f"/api/v1/tags/{tag.id}")
        assert response.status_code == 404
