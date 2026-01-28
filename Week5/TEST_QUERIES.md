# MCP 工具测试查询

用于在 Claude CLI 中测试 PostgreSQL MCP 服务器的示例查询。

## 测试环境

- **数据库**: ecommerce_small, social_medium, erp_large
- **MCP 服务器**: postgres-mcp
- **AI 模型**: 阿里百炼 qwen-turbo-latest
- **代理**: http://127.0.0.1:7890

---

## 1. 基础测试 - 列出数据库

**目标**: 验证 MCP 连接和数据库发现

**提示词**:
```
请使用 list_databases 工具列出所有可用的数据库
```

**预期结果**:
- ✅ 显示 3 个数据库: ecommerce_small, social_medium, erp_large
- ✅ 显示表数量和状态

---

## 2. Schema 获取 - 电商数据库

**目标**: 验证 schema 缓存和资源访问

**提示词**:
```
请获取 ecommerce_small 数据库的完整 schema 信息
```

**预期结果**:
- ✅ 显示所有表结构
- ✅ 显示列定义、类型、约束

---

## 3. SQL 验证 - 安全检查

**目标**: 验证 SQL 安全验证器

**提示词 1 (应该通过)**:
```
请验证这个 SQL: SELECT * FROM products LIMIT 10;
数据库: ecommerce_small
```

**提示词 2 (应该拒绝)**:
```
请验证这个 SQL: DELETE FROM products WHERE id = 1;
数据库: ecommerce_small
```

**预期结果**:
- ✅ SELECT 查询通过验证
- ✅ DELETE 查询被拒绝

---

## 4. AI SQL 生成 - 简单查询 (Easy)

**目标**: 测试自然语言转 SQL (基础)

**提示词**:
```
使用 generate_sql 工具:
自然语言: 显示所有产品的名称和价格
数据库: ecommerce_small
```

**预期 SQL**:
```sql
SELECT name, price FROM products;
```

---

## 5. AI SQL 生成 - 带条件 (Medium)

**目标**: 测试带 WHERE 子句的查询

**提示词**:
```
生成 SQL:
显示价格大于 100 的产品，按价格降序排列
数据库: ecommerce_small
```

**预期 SQL**:
```sql
SELECT * FROM products 
WHERE price > 100 
ORDER BY price DESC;
```

---

## 6. AI SQL 生成 - 聚合查询 (Medium)

**目标**: 测试 GROUP BY 和聚合函数

**提示词**:
```
生成 SQL:
统计每个类别的产品数量
数据库: ecommerce_small
```

**预期 SQL**:
```sql
SELECT category_id, COUNT(*) as product_count
FROM products
GROUP BY category_id;
```

---

## 7. 查询执行 - 直接查询

**目标**: 测试 execute_query 工具

**提示词**:
```
使用 execute_query 工具执行:
自然语言: 显示前 5 个订单的详细信息
数据库: ecommerce_small
限制: 5
```

**预期结果**:
- ✅ 返回格式化的表格
- ✅ 显示列名和数据
- ✅ 显示执行时间

---

## 8. 生成并执行 - 端到端

**目标**: 测试完整流程 (生成 + 验证 + 执行)

**提示词**:
```
使用 generate_and_execute_query:
显示最近创建的 10 个用户的用户名和邮箱
数据库: ecommerce_small
```

**预期结果**:
- ✅ 生成正确 SQL
- ✅ 通过验证
- ✅ 执行成功
- ✅ 返回数据

---

## 9. 数据库统计

**目标**: 测试统计信息获取

**提示词**:
```
获取 ecommerce_small 数据库的统计信息
```

**预期结果**:
- ✅ 表数量
- ✅ 总行数
- ✅ 索引信息

---

## 10. 复杂查询 - JOIN (Hard)

**目标**: 测试多表关联

**提示词**:
```
生成 SQL:
显示订单详情，包括用户名、产品名称和订单金额，按订单时间降序排列
数据库: ecommerce_small
限制: 10
```

**预期 SQL**:
```sql
SELECT 
    o.id as order_id,
    u.username,
    p.name as product_name,
    o.total_amount,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
ORDER BY o.created_at DESC
LIMIT 10;
```

---

## 测试检查清单

完成以下测试并记录结果：

- [ ] 1. list_databases - 数据库列表
- [ ] 2. get_schema - Schema 获取
- [ ] 3. validate_sql - SQL 验证 (通过)
- [ ] 4. validate_sql - SQL 验证 (拒绝)
- [ ] 5. generate_sql - 简单查询
- [ ] 6. generate_sql - 条件查询
- [ ] 7. generate_sql - 聚合查询
- [ ] 8. execute_query - 查询执行
- [ ] 9. generate_and_execute_query - 端到端
- [ ] 10. get_database_statistics - 统计信息
- [ ] 11. explain_query - 查询解释
- [ ] 12. generate_sql - 复杂 JOIN

---

## 故障排查

### 问题 1: MCP 服务器无法连接

**症状**: Claude 提示找不到 MCP 工具

**解决**:
```bash
# 检查 MCP 配置
echo $MCP_CONFIG_PATH

# 手动测试服务器
cd /home/ray/Documents/VibeCoding/Week5
source .venv/bin/activate
python -m postgres_mcp
```

### 问题 2: 数据库连接失败

**症状**: 提示无法连接到 PostgreSQL

**解决**:
```bash
# 检查数据库状态
cd /home/ray/Documents/VibeCoding/Week5/fixtures
docker compose ps

# 重启数据库
docker compose restart
```

### 问题 3: AI 生成失败

**症状**: generate_sql 返回错误

**解决**:
1. 检查代理设置: `echo $HTTP_PROXY`
2. 检查 API Key 配置: `cat config/config.yaml | grep api_key`
3. 检查网络连接: `curl -x http://127.0.0.1:7890 https://dashscope.aliyuncs.com`

---

**测试开始时间**: _____  
**测试完成时间**: _____  
**总体通过率**: _____ / 12
