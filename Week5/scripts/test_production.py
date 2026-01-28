#!/usr/bin/env python3
"""
PostgreSQL MCP Server - Simple Production Test
测试数据库连接和基础查询功能
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from postgres_mcp.config import Config
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner


class SimpleProductionTest:
    """简化的生产测试"""

    def __init__(self):
        self.results = {
            "test_info": {
                "date": datetime.now().isoformat(),
                "version": "0.4.0",
            },
            "database_connections": {},
            "database_statistics": {},
            "sql_validation": {},
            "direct_queries": [],
        }
        self.settings = None
        self.pool_manager = None
        self.query_runner = None
        self.sql_validator = None

    async def setup(self):
        """初始化组件"""
        print("🔧 Initializing components...")

        # Load settings
        self.settings = Config.load("config/config.yaml")
        print(f"✅ Config loaded: {len(self.settings.databases)} databases")

        # Initialize pool manager
        self.pool_manager = PoolManager(self.settings.databases)
        await self.pool_manager.initialize()
        print("✅ Pool manager initialized")

        # Initialize query components
        self.query_runner = QueryRunner(timeout_seconds=30.0)
        self.sql_validator = SQLValidator()
        print("✅ Query components initialized")

    async def test_database_connections(self):
        """测试数据库连接"""
        print("\n📊 Testing database connections...")

        for db_config in self.settings.databases:
            db_name = db_config.name
            try:
                async with self.pool_manager.get_connection(db_name) as conn:
                    version = await conn.fetchval("SELECT version()")
                    current_db = await conn.fetchval("SELECT current_database()")
                    user = await conn.fetchval("SELECT current_user")

                    self.results["database_connections"][db_name] = {
                        "status": "✅ success",
                        "database": current_db,
                        "user": user,
                        "postgresql_version": version.split(",")[0]
                        if "," in version
                        else version[:50],
                    }
                    print(f"  ✅ {db_name}: Connected to '{current_db}' as '{user}'")
            except Exception as e:
                self.results["database_connections"][db_name] = {
                    "status": "❌ error",
                    "error": str(e),
                }
                print(f"  ❌ {db_name}: {e}")

    async def test_database_statistics(self):
        """测试数据库统计信息"""
        print("\n📈 Testing database statistics...")

        for db_config in self.settings.databases:
            db_name = db_config.name
            try:
                async with self.pool_manager.get_connection(db_name) as conn:
                    # Count tables
                    table_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                    )

                    # Get table list
                    tables = await conn.fetch(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
                    )
                    table_list = [row["table_name"] for row in tables]

                    # Get row counts for each table
                    table_stats = []
                    for table_name in table_list:
                        try:
                            row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                            table_stats.append({"table": table_name, "rows": row_count})
                        except Exception as e:
                            table_stats.append({"table": table_name, "error": str(e)})

                    total_rows = sum(s.get("rows", 0) for s in table_stats)

                    self.results["database_statistics"][db_name] = {
                        "status": "✅ success",
                        "tables": table_count,
                        "total_rows": total_rows,
                        "table_details": table_stats,
                    }

                    print(f"  ✅ {db_name}: {table_count} tables, {total_rows} total rows")
                    for stat in table_stats[:5]:
                        if "rows" in stat:
                            print(f"     - {stat['table']}: {stat['rows']} rows")

            except Exception as e:
                self.results["database_statistics"][db_name] = {
                    "status": "❌ error",
                    "error": str(e),
                }
                print(f"  ❌ {db_name}: {e}")

    async def test_sql_validation(self):
        """测试 SQL 验证"""
        print("\n🔒 Testing SQL validation...")

        test_cases = [
            ("SELECT * FROM customers", True, "Simple SELECT"),
            ("SELECT * FROM customers LIMIT 10", True, "SELECT with LIMIT"),
            (
                "SELECT c.*, o.* FROM customers c JOIN orders o ON c.id = o.customer_id",
                True,
                "JOIN query",
            ),
            ("INSERT INTO customers VALUES (1, 'test')", False, "INSERT (should block)"),
            ("UPDATE customers SET name = 'test'", False, "UPDATE (should block)"),
            ("DELETE FROM customers", False, "DELETE (should block)"),
            ("DROP TABLE customers", False, "DROP TABLE (should block)"),
            ("SELECT pg_read_file('/etc/passwd')", False, "Dangerous function (should block)"),
        ]

        passed = 0
        failed = 0

        for sql, should_pass, description in test_cases:
            try:
                result = self.sql_validator.validate(sql)
                is_correct = result.valid == should_pass
                status = "✅ PASS" if is_correct else "❌ FAIL"

                self.results["sql_validation"][description] = {
                    "sql": sql,
                    "expected_valid": should_pass,
                    "actual_valid": result.valid,
                    "test_passed": is_correct,
                    "validation_errors": result.errors,
                }

                if is_correct:
                    passed += 1
                else:
                    failed += 1

                print(f"  {status} {description}")
                if result.errors and not should_pass:
                    print(f"       ↳ {result.errors[0]}")

            except Exception as e:
                failed += 1
                self.results["sql_validation"][description] = {"sql": sql, "test_error": str(e)}
                print(f"  ❌ {description}: {e}")

        print(f"\n  Summary: {passed} passed, {failed} failed")

    async def test_direct_queries(self):
        """测试直接 SQL 查询执行"""
        print("\n⚡ Testing direct SQL query execution...")

        test_queries = [
            {
                "id": "q1",
                "database": "ecommerce_small",
                "description": "List customers",
                "sql": "SELECT * FROM customers LIMIT 5",
            },
            {
                "id": "q2",
                "database": "ecommerce_small",
                "description": "Count products",
                "sql": "SELECT COUNT(*) as total FROM products",
            },
            {
                "id": "q3",
                "database": "ecommerce_small",
                "description": "Recent orders",
                "sql": "SELECT * FROM orders LIMIT 3",
            },
            {
                "id": "q4",
                "database": "ecommerce_small",
                "description": "Orders with customer names",
                "sql": "SELECT orders.order_id, orders.total_amount FROM orders LIMIT 5",
            },
            {
                "id": "q5",
                "database": "social_medium",
                "description": "List users",
                "sql": "SELECT * FROM users LIMIT 5",
            },
            {
                "id": "q6",
                "database": "social_medium",
                "description": "Count users",
                "sql": "SELECT COUNT(*) as total_users FROM users",
            },
            {
                "id": "q7",
                "database": "erp_large",
                "description": "List departments",
                "sql": "SELECT * FROM departments LIMIT 5",
            },
            {
                "id": "q8",
                "database": "erp_large",
                "description": "Count employees",
                "sql": "SELECT COUNT(*) as total_employees FROM employees",
            },
        ]

        for query in test_queries:
            try:
                # Get pool directly instead of using get_connection context manager
                pool = self.pool_manager._pools[query["database"]]
                conn = await pool.acquire()
                try:
                    result = await self.query_runner.execute(query["sql"], conn, limit=10)

                    self.results["direct_queries"].append(
                        {
                            "id": query["id"],
                            "database": query["database"],
                            "description": query["description"],
                            "status": "✅ success",
                            "sql": query["sql"],
                            "row_count": result.row_count,
                            "column_count": len(result.columns),
                            "execution_time_ms": round(result.execution_time_ms, 2),
                            "columns": [{"name": c.name, "type": c.type} for c in result.columns],
                            "sample_rows": result.rows[:2] if result.rows else [],
                        }
                    )

                    print(f"  ✅ {query['description']} ({query['database']})")
                    print(
                        f"     ↳ {result.row_count} rows, {len(result.columns)} columns, {result.execution_time_ms:.1f}ms"
                    )
                finally:
                    await pool.release(conn)

            except Exception as e:
                import traceback

                error_detail = f"{type(e).__name__}: {str(e)}"
                self.results["direct_queries"].append(
                    {
                        "id": query["id"],
                        "database": query["database"],
                        "description": query["description"],
                        "status": "❌ error",
                        "sql": query["sql"],
                        "error": error_detail,
                        "traceback": traceback.format_exc(),
                    }
                )
                print(f"  ❌ {query['description']} ({query['database']}): {error_detail}")

    async def cleanup(self):
        """清理资源"""
        print("\n🧹 Cleaning up...")
        if self.pool_manager:
            await self.pool_manager.close_all()
        print("✅ All connections closed")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("📊 PRODUCTION TEST SUMMARY")
        print("=" * 70)
        print(f"Test Date: {self.results['test_info']['date']}")
        print(f"Version: {self.results['test_info']['version']}")

        # Database connections
        db_conn = self.results["database_connections"]
        db_success = sum(1 for r in db_conn.values() if "success" in r["status"])
        db_total = len(db_conn)
        print(f"\n✅ Database Connections: {db_success}/{db_total} passed")
        for db_name, result in db_conn.items():
            print(f"   - {db_name}: {result['status']}")

        # Database statistics
        db_stats = self.results["database_statistics"]
        stats_success = sum(1 for r in db_stats.values() if "success" in r["status"])
        stats_total = len(db_stats)
        print(f"\n✅ Database Statistics: {stats_success}/{stats_total} passed")
        for db_name, result in db_stats.items():
            if "success" in result["status"]:
                print(f"   - {db_name}: {result['tables']} tables, {result['total_rows']} rows")

        # SQL validation
        sql_val = self.results["sql_validation"]
        val_success = sum(1 for r in sql_val.values() if r.get("test_passed", False))
        val_total = len(sql_val)
        print(f"\n✅ SQL Validation: {val_success}/{val_total} passed")

        # Direct queries
        queries = self.results["direct_queries"]
        query_success = sum(1 for r in queries if "success" in r["status"])
        query_total = len(queries)
        print(f"\n✅ Direct Queries: {query_success}/{query_total} passed")

        # Overall
        total_success = db_success + stats_success + val_success + query_success
        total_tests = db_total + stats_total + val_total + query_total
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{'='*70}")
        print(f"🎯 OVERALL: {total_success}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"{'='*70}\n")

        # Save results
        output_path = Path("test_results_production.json")
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"📄 Detailed results saved to: {output_path}")

    async def run(self):
        """运行所有测试"""
        try:
            await self.setup()
            await self.test_database_connections()
            await self.test_database_statistics()
            await self.test_sql_validation()
            await self.test_direct_queries()
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await self.cleanup()
            self.print_summary()


async def main():
    """主函数"""
    print("=" * 70)
    print("PostgreSQL MCP Server - Simple Production Test")
    print("Testing: Connections, Statistics, Validation, Queries")
    print("=" * 70)

    test = SimpleProductionTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())
