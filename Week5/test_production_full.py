#!/usr/bin/env python3
"""
完整生产环境测试 - 通义千问 AI SQL 生成

测试范围:
1. 配置加载和验证
2. 数据库连接
3. AI SQL 生成 (通义千问)
4. SQL 验证
5. 查询执行

Author: AI Assistant
Date: 2026-01-29
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.config import Config
from postgres_mcp.db.connection_pool import ConnectionPool
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.core.sql_validator import SQLValidator


class FullProductionTester:
    """完整生产测试器 - 包含 AI 生成"""

    def __init__(self):
        self.config = None
        self.ai_client = None
        self.pools = {}
        self.sql_validator = SQLValidator()
        self.results = {
            "config": {},
            "databases": {},
            "ai_tests": [],
            "query_tests": [],
        }

    async def setup(self):
        """初始化"""
        print("=" * 80)
        print("🚀 PostgreSQL MCP Server - 完整生产测试 (通义千问)")
        print("=" * 80)
        print()

        # 1. 加载配置
        print("📋 1. 加载配置...")
        self.config = Config.load("config/config.yaml")
        print(f"   ✅ 配置加载成功")
        print(f"   - AI 模型: {self.config.openai.model}")
        print(f"   - Base URL: {self.config.openai.base_url}")
        print(f"   - 数据库数量: {len(self.config.databases)}")
        self.results["config"] = {
            "model": self.config.openai.model,
            "base_url": self.config.openai.base_url,
            "databases": len(self.config.databases),
        }

        # 2. 初始化 AI 客户端
        print("\n🤖 2. 初始化 AI 客户端...")
        self.ai_client = OpenAIClient(
            api_key=self.config.openai.resolved_api_key,
            model=self.config.openai.model,
            temperature=self.config.openai.temperature,
            max_tokens=self.config.openai.max_tokens,
            timeout=self.config.openai.timeout,
            base_url=self.config.openai.base_url,
        )
        print(f"   ✅ AI 客户端初始化成功")

        # 3. 初始化数据库连接
        print("\n🔌 3. 初始化数据库连接...")
        for db_name, db_config in self.config.databases.items():
            pool = ConnectionPool(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.user,
                password=db_config.password,
                min_size=db_config.min_pool_size,
                max_size=db_config.max_pool_size,
            )
            await pool.initialize()
            self.pools[db_name] = pool
            print(f"   ✅ {db_name} 连接池已初始化")

    async def test_databases(self):
        """测试数据库连接"""
        print("\n" + "=" * 80)
        print("📊 数据库连接测试")
        print("=" * 80)

        for db_name, pool in self.pools.items():
            print(f"\n🗄️  测试: {db_name}")
            try:
                conn = await pool.acquire()
                result = await conn.fetch("SELECT COUNT(*) FROM pg_tables WHERE schemaname='public'")
                table_count = result[0]['count']
                await pool.release(conn)

                self.results["databases"][db_name] = {
                    "status": "✅ 成功",
                    "table_count": table_count,
                }
                print(f"   ✅ 连接成功 - 表数量: {table_count}")
            except Exception as e:
                self.results["databases"][db_name] = {"status": f"❌ 失败: {e}"}
                print(f"   ❌ 连接失败: {e}")

    async def test_ai_generation(self):
        """测试 AI SQL 生成"""
        print("\n" + "=" * 80)
        print("🤖 AI SQL 生成测试 (通义千问)")
        print("=" * 80)

        # 加载示例
        examples_file = Path("examples/sample_queries.json")
        if not examples_file.exists():
            print(f"   ⚠️  示例文件不存在,跳过 AI 测试")
            return

        with open(examples_file) as f:
            data = json.load(f)

        # 测试前5个示例
        examples = data["examples"][:5]
        print(f"\n测试 {len(examples)} 个示例查询:\n")

        for i, example in enumerate(examples, 1):
            nl_query = example["natural_language"]
            db_name = example["database"]
            difficulty = example["difficulty"]

            print(f"{i}. [{difficulty.upper()}] {nl_query}")

            test_result = {
                "query": nl_query,
                "database": db_name,
                "difficulty": difficulty,
            }

            try:
                # 获取 schema
                db_config = self.config.databases[db_name]
                inspector = SchemaInspector(
                    host=db_config.host,
                    port=db_config.port,
                    user=db_config.user,
                    password=db_config.password,
                    database=db_config.database,
                )
                await inspector.connect()
                schema = await inspector.get_full_schema()
                await inspector.close()

                # 生成 SQL
                sql = await self.ai_client.generate_sql(nl_query, schema)
                test_result["generated_sql"] = sql

                # 验证 SQL
                validation = self.sql_validator.validate(sql)
                test_result["validation"] = validation.valid

                if validation.valid:
                    print(f"   ✅ 生成成功: {sql[:70]}...")
                    test_result["status"] = "✅ 成功"
                else:
                    print(f"   ⚠️  验证失败: {', '.join(validation.errors)}")
                    test_result["status"] = "⚠️  验证失败"

            except Exception as e:
                print(f"   ❌ 失败: {e}")
                test_result["status"] = f"❌ 失败"
                test_result["error"] = str(e)

            self.results["ai_tests"].append(test_result)
            print()

    async def test_query_execution(self):
        """测试查询执行"""
        print("=" * 80)
        print("⚡ 查询执行测试")
        print("=" * 80)
        print()

        test_queries = [
            ("ecommerce_small", "SELECT COUNT(*) as user_count FROM users"),
            ("ecommerce_small", "SELECT * FROM products LIMIT 3"),
            ("social_medium", "SELECT COUNT(*) as user_count FROM users"),
        ]

        for db_name, sql in test_queries:
            print(f"📝 {db_name}: {sql}")
            test_result = {"database": db_name, "sql": sql}

            try:
                # 验证
                validation = self.sql_validator.validate(sql)
                if not validation.valid:
                    print(f"   ❌ SQL 验证失败: {', '.join(validation.errors)}")
                    test_result["status"] = "❌ 验证失败"
                    continue

                # 执行
                pool = self.pools[db_name]
                conn = await pool.acquire()
                result = await conn.fetch(sql)
                await pool.release(conn)

                print(f"   ✅ 成功 - 返回 {len(result)} 行")
                test_result["status"] = "✅ 成功"
                test_result["row_count"] = len(result)

            except Exception as e:
                print(f"   ❌ 失败: {e}")
                test_result["status"] = "❌ 失败"
                test_result["error"] = str(e)

            self.results["query_tests"].append(test_result)
            print()

    async def cleanup(self):
        """清理资源"""
        print("=" * 80)
        print("🧹 清理资源")
        print("=" * 80)

        for db_name, pool in self.pools.items():
            await pool.close()
            print(f"   ✅ {db_name} 连接池已关闭")

    def generate_report(self):
        """生成最终报告"""
        print("\n" + "=" * 80)
        print("📊 测试报告")
        print("=" * 80)

        # 配置
        print(f"\n✅ 配置:")
        print(f"   - AI 模型: {self.results['config']['model']}")
        print(f"   - Base URL: {self.results['config']['base_url']}")

        # 数据库
        print(f"\n✅ 数据库连接: {len(self.results['databases'])} 个")
        for db, result in self.results['databases'].items():
            print(f"   - {db}: {result['status']}")

        # AI 生成
        if self.results["ai_tests"]:
            success = sum(1 for t in self.results["ai_tests"] if t["status"] == "✅ 成功")
            total = len(self.results["ai_tests"])
            print(f"\n✅ AI SQL 生成:")
            print(f"   - 成功率: {success}/{total} ({success/total*100:.1f}%)")

        # 查询执行
        if self.results["query_tests"]:
            success = sum(1 for t in self.results["query_tests"] if t["status"] == "✅ 成功")
            total = len(self.results["query_tests"])
            print(f"\n✅ 查询执行:")
            print(f"   - 成功率: {success}/{total} ({success/total*100:.1f}%)")

        print("\n" + "=" * 80)
        print("🎉 测试完成!")
        print("=" * 80)


async def main():
    """主流程"""
    tester = FullProductionTester()

    try:
        await tester.setup()
        await tester.test_databases()
        await tester.test_ai_generation()
        await tester.test_query_execution()
    finally:
        await tester.cleanup()

    tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
