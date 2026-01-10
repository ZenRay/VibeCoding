#!/usr/bin/env python3
"""API 测试脚本"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_VERSION = "v1"

def print_test(name, response):
    """打印测试结果"""
    print(f"\n{'=' * 60}")
    print(f"{name}")
    print(f"{'=' * 60}")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"响应: {response.text}")

def main():
    print("Week2 数据库查询工具 - API 测试")
    print("=" * 60)

    # 1. 健康检查
    response = requests.get(f"{BASE_URL}/health")
    print_test("1. 健康检查", response)

    # 2. 获取所有数据库连接（应为空）
    response = requests.get(f"{BASE_URL}/api/{API_VERSION}/dbs")
    print_test("2. 获取所有数据库连接（初始）", response)

    # 3. 添加 PostgreSQL 连接
    response = requests.put(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres",
        json={"url": "postgresql://postgres:postgres@localhost:5432/testdb"}
    )
    print_test("3. 添加 PostgreSQL 连接", response)

    # 4. 添加 MySQL 连接
    response = requests.put(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-mysql",
        json={"url": "mysql://testuser:testpass@localhost:3306/testdb"}
    )
    print_test("4. 添加 MySQL 连接", response)

    # 5. 添加 SQLite 连接
    response = requests.put(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-sqlite",
        json={"url": "sqlite:///data/test.db"}
    )
    print_test("5. 添加 SQLite 连接", response)

    # 6. 再次获取所有数据库连接
    response = requests.get(f"{BASE_URL}/api/{API_VERSION}/dbs")
    print_test("6. 获取所有数据库连接（应有 3 个）", response)

    # 7. 获取 PostgreSQL 元数据
    response = requests.get(f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres")
    print_test("7. 获取 PostgreSQL 元数据", response)

    # 8. 执行简单 SELECT 查询
    response = requests.post(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres/query",
        json={"sql": "SELECT 1 as test_number, 'Hello World' as test_string"}
    )
    print_test("8. 执行简单 SELECT 查询", response)

    # 9. 测试 SQL 注入防护 - 注释
    response = requests.post(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres/query",
        json={"sql": "SELECT * FROM users -- WHERE role='admin'"}
    )
    print_test("9. 测试 SQL 注入防护 - 注释（应被拒绝）", response)

    # 10. 测试 SQL 注入防护 - 多语句
    response = requests.post(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres/query",
        json={"sql": "SELECT * FROM users; DROP TABLE users"}
    )
    print_test("10. 测试 SQL 注入防护 - 多语句（应被拒绝）", response)

    # 11. 测试非 SELECT 语句 - INSERT
    response = requests.post(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres/query",
        json={"sql": "INSERT INTO users (name, email) VALUES ('test', 'test@example.com')"}
    )
    print_test("11. 测试非 SELECT 语句 - INSERT（应被拒绝）", response)

    # 12. 测试非 SELECT 语句 - UPDATE
    response = requests.post(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres/query",
        json={"sql": "UPDATE users SET role = 'admin' WHERE id = 1"}
    )
    print_test("12. 测试非 SELECT 语句 - UPDATE（应被拒绝）", response)

    # 13. 测试非 SELECT 语句 - DELETE
    response = requests.post(
        f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres/query",
        json={"sql": "DELETE FROM users WHERE id = 1"}
    )
    print_test("13. 测试非 SELECT 语句 - DELETE（应被拒绝）", response)

    # 14. 测试获取不存在的连接
    response = requests.get(f"{BASE_URL}/api/{API_VERSION}/dbs/non-existent-db")
    print_test("14. 测试获取不存在的连接（404）", response)

    # 15. 删除 SQLite 连接
    response = requests.delete(f"{BASE_URL}/api/{API_VERSION}/dbs/test-sqlite")
    print_test("15. 删除 SQLite 连接", response)

    # 16. 验证删除
    response = requests.get(f"{BASE_URL}/api/{API_VERSION}/dbs/test-sqlite")
    print_test("16. 验证删除（应返回 404）", response)

    # 清理：删除测试连接
    print("\n" + "=" * 60)
    print("清理测试数据...")
    print("=" * 60)
    requests.delete(f"{BASE_URL}/api/{API_VERSION}/dbs/test-postgres")
    requests.delete(f"{BASE_URL}/api/{API_VERSION}/dbs/test-mysql")
    print("测试完成！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)
