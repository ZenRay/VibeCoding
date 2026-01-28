# Instructions
- 后端使用 Ergonomic Python 风格来编写代码，前端使用 typescript
- 前后端都要有严格的类型标注
- 使用 pydantic 来定义数据模型
- 所有后端生成的 JSON 数据，使用 camelCase 格式。
- 不需要 authentication，任何用户都可以使用。
  
## code review command

帮我参照 @.claude/commands/speckit.specify.md 的结构，think ultra hard，构建一个对 Python 和 Typescript 代码进行深度代码审查的命令，放在 @.claude/commands/ 下。主要考虑几个方面：

- 架构和设计：是否考虑 python 和 typescript 的架构和设计最佳实践？是否有清晰的接口设计？是否考虑一定程度的可扩展性
- KISS 原则
- 代码质量：DRY, YAGNI, SOLID, etc. 函数原则上不超过 150 行，参数原则上不超过 7 个。
- 使用 builder 模式




## 添加一个中间任务
/speckit.specify 参考backend中的PostgreSQL实现 MySQL的metadata提取和查询支持,同时自然语言生成sql也支
持MySQL。数据库的服务需要一样放在 env 中的docker compose 服务中。支持查询 mysql 中的数据。生成的任务文件放到 specs 下生成 002 的任务



目前mysql已经得到支持,在 fixtures/tcest.rest中添加MySQLdb支持的测试用例,然后运行测试。然后运行测试。如果后
端测试 ok,那么打开后端和前端,使用 playwright测试前端,确保MySQLdb的基本功能:
- 添加 新的数据库 interview_db (url为mysql://root@loo:alhost:3306/interview_db)
-生成sql,查询interview_db,并显示结果
-自然语言生成MySQLsql,查询interview_db,并显示结结果