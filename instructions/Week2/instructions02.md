# Plan

- 后端使用 Python (uv) / FastAPI / sqlglot / openai sdk 来实现。
- 前端使用 React / refine 5 / tailwind / ant design 来实现。sql editor 使用 monaco editor 来实现。
- 准备测试用的用例、数据等

OpenAI API key 在环境变量 OPENAI_API_KEY 中。数据库连接和 metadata 存储在 sqlite 数据库中，放在 Week2/data/meta.db 中。



后端 API 需要支持 cors，允许所有 origin。大致 API 如下：

```bash
# 获取所有已存储的数据库
GET /api/v1/dbs
# 添加一个数据库
PUT /api/v1/dbs/{name}

{
  "url": "postgres://postgres:postgres@localhost:5432/postgres"
}

# 获取一个数据库的 metadata
GET /api/v1/dbs/{name}

# 查询某个数据库的信息
POST /api/v1/dbs/{name}/query

{
  "sql": "SELECT * FROM users"
}

# 根据自然语言生成 sql
POST /api/v1/dbs/{name}/query/natural

{
  "prompt": "查询用户表的所有信息"
}
```
