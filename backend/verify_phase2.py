#!/usr/bin/env python3
"""阶段 2 验证脚本

用于验证阶段 2 的所有 API 端点是否正常工作
"""

import sys
import requests
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def check_health():
    """检查健康检查端点"""
    print("🔍 检查健康检查端点...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ 健康检查通过")
            return True
        else:
            print(f"  ❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 无法连接到服务器: {e}")
        print("     请确保后端服务已启动: uvicorn app.main:app --reload")
        return False

def check_api_docs():
    """检查 API 文档"""
    print("\n🔍 检查 API 文档...")
    try:
        # 检查 Swagger UI
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("  ✅ Swagger UI 可访问: http://localhost:8000/docs")
        else:
            print(f"  ❌ Swagger UI 不可访问: {response.status_code}")
            return False

        # 检查 ReDoc
        response = requests.get(f"{BASE_URL}/redoc", timeout=5)
        if response.status_code == 200:
            print("  ✅ ReDoc 可访问: http://localhost:8000/redoc")
        else:
            print(f"  ⚠️  ReDoc 不可访问: {response.status_code}")

        # 检查 OpenAPI JSON
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            paths = data.get("paths", {})
            print(f"  ✅ OpenAPI JSON 可访问，包含 {len(paths)} 个端点")
            return True
        else:
            print(f"  ❌ OpenAPI JSON 不可访问: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 检查 API 文档失败: {e}")
        return False

def test_tag_api():
    """测试 Tag API"""
    print("\n🔍 测试 Tag API...")
    
    try:
        # 创建标签
        print("  1. 创建标签...")
        response = requests.post(
            f"{API_BASE}/tags",
            json={"name": "verify_test", "color": "#FF0000"},
            timeout=5
        )
        if response.status_code == 201:
            tag_data = response.json()
            tag_id = tag_data["id"]
            print(f"     ✅ 标签创建成功，ID: {tag_id}")
            print(f"     注意：名称已自动转大写: {tag_data['name']}")
        else:
            print(f"     ❌ 创建标签失败: {response.status_code}")
            print(f"     响应: {response.text}")
            return False

        # 获取标签列表
        print("  2. 获取标签列表...")
        response = requests.get(f"{API_BASE}/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"     ✅ 获取标签列表成功，共 {len(data.get('data', []))} 个标签")
        else:
            print(f"     ❌ 获取标签列表失败: {response.status_code}")
            return False

        # 获取单个标签
        print("  3. 获取单个标签...")
        response = requests.get(f"{API_BASE}/tags/{tag_id}", timeout=5)
        if response.status_code == 200:
            print("     ✅ 获取单个标签成功")
        else:
            print(f"     ❌ 获取单个标签失败: {response.status_code}")
            return False

        return tag_id
    except Exception as e:
        print(f"  ❌ Tag API 测试失败: {e}")
        return None

def test_ticket_api(tag_id):
    """测试 Ticket API"""
    print("\n🔍 测试 Ticket API...")
    
    try:
        # 创建 Ticket
        print("  1. 创建 Ticket...")
        response = requests.post(
            f"{API_BASE}/tickets",
            json={
                "title": "验证测试 Ticket",
                "description": "用于验证 API 的测试 Ticket",
                "tag_ids": [tag_id] if tag_id else None,
            },
            timeout=5
        )
        if response.status_code == 201:
            ticket_data = response.json()
            ticket_id = ticket_data["id"]
            print(f"     ✅ Ticket 创建成功，ID: {ticket_id}")
        else:
            print(f"     ❌ 创建 Ticket 失败: {response.status_code}")
            print(f"     响应: {response.text}")
            return False

        # 获取 Ticket 列表
        print("  2. 获取 Ticket 列表...")
        response = requests.get(f"{API_BASE}/tickets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"     ✅ 获取 Ticket 列表成功，共 {len(data.get('data', []))} 个 Ticket")
        else:
            print(f"     ❌ 获取 Ticket 列表失败: {response.status_code}")
            return False

        # 获取单个 Ticket
        print("  3. 获取单个 Ticket...")
        response = requests.get(f"{API_BASE}/tickets/{ticket_id}", timeout=5)
        if response.status_code == 200:
            print("     ✅ 获取单个 Ticket 成功")
        else:
            print(f"     ❌ 获取单个 Ticket 失败: {response.status_code}")
            return False

        # 更新 Ticket
        print("  4. 更新 Ticket...")
        response = requests.put(
            f"{API_BASE}/tickets/{ticket_id}",
            json={"title": "更新后的标题"},
            timeout=5
        )
        if response.status_code == 200:
            print("     ✅ 更新 Ticket 成功")
        else:
            print(f"     ❌ 更新 Ticket 失败: {response.status_code}")
            return False

        # 切换状态
        print("  5. 切换 Ticket 状态...")
        response = requests.patch(f"{API_BASE}/tickets/{ticket_id}/toggle-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"     ✅ 状态切换成功，当前状态: {data['status']}")
        else:
            print(f"     ❌ 状态切换失败: {response.status_code}")
            return False

        # 搜索 Ticket
        print("  6. 搜索 Ticket...")
        response = requests.get(f"{API_BASE}/tickets?search=验证", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"     ✅ 搜索成功，找到 {len(data.get('data', []))} 个结果")
        else:
            print(f"     ❌ 搜索失败: {response.status_code}")
            return False

        # 软删除 Ticket
        print("  7. 软删除 Ticket...")
        response = requests.delete(f"{API_BASE}/tickets/{ticket_id}", timeout=5)
        if response.status_code == 204:
            print("     ✅ 软删除成功")
        else:
            print(f"     ❌ 软删除失败: {response.status_code}")
            return False

        # 查看回收站
        print("  8. 查看回收站...")
        response = requests.get(f"{API_BASE}/tickets?only_deleted=true", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"     ✅ 回收站查看成功，共 {len(data.get('data', []))} 个已删除的 Ticket")
        else:
            print(f"     ❌ 查看回收站失败: {response.status_code}")
            return False

        # 恢复 Ticket
        print("  9. 恢复 Ticket...")
        response = requests.post(f"{API_BASE}/tickets/{ticket_id}/restore", timeout=5)
        if response.status_code == 200:
            print("     ✅ 恢复成功")
        else:
            print(f"     ❌ 恢复失败: {response.status_code}")
            return False

        return True
    except Exception as e:
        print(f"  ❌ Ticket API 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("阶段 2 验证脚本")
    print("=" * 60)
    print()

    results = []

    # 检查健康检查
    results.append(("健康检查", check_health()))
    if not results[-1][1]:
        print("\n❌ 无法连接到服务器，请先启动后端服务")
        return 1

    # 检查 API 文档
    results.append(("API 文档", check_api_docs()))

    # 测试 Tag API
    tag_id = test_tag_api()
    results.append(("Tag API", tag_id is not None))

    # 测试 Ticket API
    if tag_id:
        results.append(("Ticket API", test_ticket_api(tag_id)))
    else:
        results.append(("Ticket API", False))

    # 总结
    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查通过！阶段 2 已完成。")
        print("\n下一步：")
        print("  1. 访问 Swagger UI: http://localhost:8000/docs")
        print("  2. 运行完整测试: pytest")
        print("  3. 开始阶段 4：实现前端 UI 组件")
    else:
        print("⚠️  部分检查未通过，请根据上述提示修复问题。")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
