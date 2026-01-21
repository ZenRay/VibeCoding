


## 测试

仔细阅读 ./w2/db_query 下面的代码，然后运行后端和前端，根据@w2/db_query/fixtures/test.rest 用 curl 测试后端已实现的路由；然后用 playwright 开前端进行测试，任何测试问题，think ultra hard and fix

## db migration & unit test

`make setup` 会出错，修复它；确保前后端 unit test 都通过。

## 添加 MySQL db 支持

参考 ./w2/db_query/backend 中的 PostgreSQL 实现，实现 MySQL 的 metadata 提取和查询支持，同时自然语言生成 sql 也支持 MySQL。目前我本地有一个 todo_db 数据库，使用 `mysql -u root todo_db -e "SELECT * FROM todos;"` 可以查询到数据。

## 测试 MySQL db 支持

目前 mysql 已经得到支持，在 ./w2/db_query/fixtures/test.rest 中添加 MySQL db 支持的测试用例，然后运行测试。如果后端测试 ok，那么打开后端和前端，使用 playwright 测试前端，确保 MySQL db 的基本功能：

- 添加 新的数据库 interview_db（url 为 mysql://root@localhost:3306/interview_db）
- 生成 sql，查询 interview_db，并显示结果
- 自然语言生成 MySQL sql，查询 interview_db，并显示结果
